from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Source


def save(client, suffix="idea"):
    response = client.post("/api/sources", json={"url": f"https://example.com/{suffix}", "title": "Original"})
    assert response.status_code == 201
    return response.json()


def version(source):
    return {"expected_updated_at": source["updated_at"]}


def test_edit_persists_preserves_identity_and_can_clear_title(client, database):
    source = save(client)
    response = client.patch(f'/api/sources/{source["id"]}', json={**version(source), "title": "  Nuevo título  "})
    assert response.status_code == 200
    edited = response.json()
    assert edited["title"] == "Nuevo título"
    assert edited["updated_at"] != source["updated_at"]
    assert edited["original_url"] == source["original_url"]
    assert edited["created_at"] == source["created_at"]
    # New DB connection observes the committed title, independently of the request session.
    database[0].dispose()
    with Session(database[0]) as session:
        assert session.get(Source, UUID(source["id"])).title == "Nuevo título"
    blank = client.patch(f'/api/sources/{source["id"]}', json={**version(edited), "title": "  "})
    assert blank.status_code == 200 and blank.json()["title"] is None


def test_trash_restore_and_duplicate_offer_preserve_same_record(client, database):
    source = save(client)
    trashed = client.request("DELETE", f'/api/sources/{source["id"]}', json=version(source))
    assert trashed.status_code == 200 and trashed.json()["deleted_at"]
    assert client.get(f'/api/sources/{source["id"]}').status_code == 404
    assert client.get("/api/sources").json()["total"] == 0
    page = client.get("/api/sources?view=trash").json()
    assert page["total"] == page["trash_total"] == 1 and page["active_total"] == 0
    assert page["items"][0]["id"] == source["id"]
    duplicate = client.post("/api/sources", json={"url": source["original_url"]})
    assert duplicate.status_code == 409
    assert duplicate.json()["existing_source"]["id"] == source["id"]
    assert client.patch(f'/api/sources/{source["id"]}', json={**version(trashed.json()), "title": "Ignored"}).status_code == 409
    # Repeating a delete after a lost response does not change the stored timestamp.
    assert client.request("DELETE", f'/api/sources/{source["id"]}', json=version(source)).json() == trashed.json()
    database[0].dispose()
    with Session(database[0]) as session:
        assert session.get(Source, UUID(source["id"])).deleted_at is not None
        assert session.scalar(select(func.count()).select_from(Source)) == 1
    restored = client.post(f'/api/sources/{source["id"]}/restore', json=version(trashed.json()))
    assert restored.status_code == 200 and restored.json()["deleted_at"] is None
    assert restored.json()["id"] == source["id"] and restored.json()["title"] == "Original"
    assert restored.json()["created_at"] == source["created_at"]
    assert client.get("/api/sources?view=trash").json()["total"] == 0
    assert client.post(f'/api/sources/{source["id"]}/restore', json=version(trashed.json())).json() == restored.json()
    database[0].dispose()
    assert client.get(f'/api/sources/{source["id"]}').json() == restored.json()
    assert client.get("/api/health").json()["processing"]["state"] == "stopped"


def test_pagination_traverses_tied_dates_and_clamps_after_last_item_removed(client, database):
    with Session(database[0]) as session:
        for number in range(41):
            session.add(Source(source_type="url", platform="other", original_url=f"https://example.com/{number}"))
        session.commit()  # All rows intentionally share the same transaction timestamp.
    pages = [client.get(f"/api/sources?offset={offset}").json() for offset in (0, 20, 40)]
    assert [len(page["items"]) for page in pages] == [20, 20, 1]
    ids = [row["id"] for page in pages for row in page["items"]]
    assert len(set(ids)) == 41
    with database[0].connect() as connection:
        expected = connection.scalars(text("SELECT id FROM sources ORDER BY created_at DESC, id DESC")).all()
    assert ids == [str(item) for item in expected]
    last = pages[-1]["items"][0]
    assert client.request("DELETE", f'/api/sources/{last["id"]}', json=version(last)).status_code == 200
    clamped = client.get("/api/sources?offset=40").json()
    assert clamped["offset"] == 20 and len(clamped["items"]) == 20 and clamped["total"] == 40
    assert client.get("/api/sources?view=trash&offset=1000").json()["offset"] == 0


@pytest.mark.parametrize("query", ["offset=-1", "offset=2147483648", "limit=0", "view=everything"])
def test_invalid_pages_are_rejected(client, query):
    assert client.get(f"/api/sources?{query}").status_code == 422


@pytest.mark.parametrize("payload", [{}, {"title": "x"}, {"title": "x" * 241}, {"title": "ok", "url": "https://example.com/changed"}, {"title": "ok", "status": "ready"}])
def test_invalid_edit_never_changes_source(client, payload):
    source = save(client)
    # Missing-version case is tested separately from invalid title/extra field cases.
    body = payload if payload == {"title": "x"} else {**version(source), **payload}
    assert client.patch(f'/api/sources/{source["id"]}', json=body).status_code == 422
    assert client.get(f'/api/sources/{source["id"]}').json() == source


def test_stale_edits_and_deletes_do_not_overwrite_newer_work(client):
    source = save(client)
    edited = client.patch(f'/api/sources/{source["id"]}', json={**version(source), "title": "Actual"}).json()
    assert client.patch(f'/api/sources/{source["id"]}', json={**version(source), "title": "Antiguo"}).status_code == 409
    assert client.request("DELETE", f'/api/sources/{source["id"]}', json=version(source)).status_code == 409
    assert client.get(f'/api/sources/{source["id"]}').json() == edited


def test_concurrent_edits_have_one_winner(client):
    source = save(client)
    def edit(title):
        return client.patch(f'/api/sources/{source["id"]}', json={**version(source), "title": title})
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(edit, ["Ventana A", "Ventana B"]))
    assert sorted(response.status_code for response in responses) == [200, 409]
    winner = next(response.json() for response in responses if response.status_code == 200)
    assert client.get(f'/api/sources/{source["id"]}').json() == winner


def test_missing_sources_and_external_mutations(client):
    source = save(client)
    for method, path, payload in [
        ("PATCH", "", {**version(source), "title": "Changed"}),
        ("DELETE", "", version(source)), ("POST", "/restore", version(source)),
    ]:
        assert client.request(method, f"/api/sources/{uuid4()}{path}", json=payload).status_code == 404
        assert client.request(method, f'/api/sources/{source["id"]}{path}', json=payload, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.get(f'/api/sources/{source["id"]}').json() == source
