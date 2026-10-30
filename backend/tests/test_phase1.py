from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

import pytest
from alembic import command
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import MediaAsset, MediaFile, ProcessingJob, Source
from app.media import storage_path
from test_library import save, version

# Header fixtures test ingestion, not codec decoding (reserved for the media engine).
VIDEO = b"\x00\x00\x00\x18ftypmp42" + b"test-video-content" * 100


def upload(client, content=VIDEO, name="prueba.mp4", source=None):
    params = {"filename": name}
    if source:
        params.update(source_id=source["id"], expected_updated_at=source["updated_at"])
    return client.post("/api/imports", params=params, content=content, headers={"Content-Type": "application/octet-stream"})


def organize(client, source, tags=None, categories=None):
    return client.put(f'/api/sources/{source["id"]}/organization', json={**version(source), "tags": tags or [], "categories": categories or []})


def test_import_copy_duplicate_and_new_connection(client, database, media_root):
    source = upload(client).json()
    assert source["source_type"] == "file" and source["original_url"] is None
    assert source["job"]["status"] == "pending"
    asset = source["assets"][0]
    assert asset["file"]["size_bytes"] == len(VIDEO)
    assert "local_path" not in str(source)
    database[0].dispose()
    assert client.get(f'/api/sources/{source["id"]}').json() == source
    assert client.get(f'/api/assets/{asset["id"]}/content').content == VIDEO
    partial = client.get(f'/api/assets/{asset["id"]}/content', headers={"Range": "bytes=0-11"})
    assert partial.status_code == 206 and partial.content == VIDEO[:12]
    assert upload(client, name="otro-nombre.mp4").status_code == 409
    assert len(list(media_root.glob("media/*/*"))) == 1
    assert list(media_root.glob("staging/*")) == []


def test_shared_content_keeps_provenance_trash_and_restore(client, database, media_root):
    local = upload(client).json()
    link = save(client)
    attached = upload(client, source=link).json()
    assert attached["original_url"] == link["original_url"]
    assert attached["assets"][0]["file"] == local["assets"][0]["file"]
    with Session(database[0]) as session:
        assert session.scalar(select(func.count()).select_from(MediaFile)) == 1
        assert session.scalar(select(func.count()).select_from(MediaAsset)) == 2
    trashed = client.request("DELETE", f'/api/sources/{local["id"]}', json=version(local)).json()
    assert client.get(f'/api/assets/{local["assets"][0]["id"]}/content').status_code == 404
    assert client.get(f'/api/assets/{attached["assets"][0]["id"]}/content').content == VIDEO
    duplicate = upload(client)
    assert duplicate.status_code == 409 and duplicate.json()["existing_source"]["id"] == local["id"]
    restored = client.post(f'/api/sources/{local["id"]}/restore', json=version(trashed)).json()
    assert restored["assets"] == local["assets"]
    assert len(list(media_root.glob("media/*/*"))) == 1


@pytest.mark.parametrize("name,content,code", [("../bad.mp4", VIDEO, 422), ("C:\\bad.mp4", VIDEO, 422), ("bad.exe", VIDEO, 415), ("fake.mp4", b"no video", 415), ("empty.mp4", b"", 415)])
def test_bad_files_leave_no_rows_or_copies(client, media_root, name, content, code):
    assert upload(client, content, name).status_code == code
    assert client.get("/api/sources").json()["total"] == 0
    assert list(media_root.glob("media/*/*")) == []
    assert list(media_root.glob("staging/*")) == []


def test_size_limit_header_and_stream(client, monkeypatch, media_root):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 20)
    assert upload(client).status_code == 413
    response = client.post("/api/imports?filename=test.mp4", content=iter([VIDEO[:12], VIDEO[12:]]))
    assert response.status_code == 413
    assert list(media_root.glob("staging/*")) == []


def test_interrupted_upload_leaves_no_source_or_temporary(client, database, media_root):
    import asyncio
    from starlette.requests import Request, ClientDisconnect
    from app.media import import_video
    messages = iter([
        {"type": "http.request", "body": VIDEO[:12], "more_body": True},
        {"type": "http.disconnect"},
    ])
    async def receive():
        return next(messages)
    request = Request({"type": "http", "headers": []}, receive)
    with Session(database[0]) as session, pytest.raises(ClientDisconnect):
        asyncio.run(import_video(request, filename="test.mp4", source_id=None, expected_updated_at=None, session=session))
    assert client.get("/api/sources").json()["total"] == 0
    assert list(media_root.glob("staging/*")) == []


def test_disk_failure_preserves_library_and_retry(client, monkeypatch, media_root):
    from app import media
    original = media.publish_file
    def fail(*args):
        raise OSError("private-path-do-not-show")
    monkeypatch.setattr(media, "publish_file", fail)
    response = upload(client)
    assert response.status_code == 507 and "private-path" not in response.text
    assert client.get("/api/sources").json()["total"] == 0
    monkeypatch.setattr(media, "publish_file", original)
    assert upload(client).status_code == 201


@pytest.mark.parametrize("committed", [False, True])
def test_lost_commit_response_is_recoverable_without_deleting_media(client, monkeypatch, media_root, committed):
    original = Session.commit
    def fail(session):
        if committed:
            original(session)
        raise SQLAlchemyError("private-connection-detail")
    monkeypatch.setattr(Session, "commit", fail)
    result = upload(client)
    assert result.status_code == 503 and "private-connection" not in result.text
    assert len(list(media_root.glob("media/*/*"))) == 1
    monkeypatch.setattr(Session, "commit", original)
    retry = upload(client)
    assert retry.status_code == (409 if committed else 201)
    page = client.get("/api/sources").json()
    assert page["total"] == 1
    asset = page["items"][0]["assets"][0]
    assert client.get(f'/api/assets/{asset["id"]}/content').content == VIDEO


def test_missing_managed_file_is_reported_and_reimport_repairs(client, media_root):
    source = upload(client).json()
    path = next(media_root.glob("media/*/*"))
    path.unlink()
    endpoint = f'/api/assets/{source["assets"][0]["id"]}/content'
    assert client.get(endpoint).status_code == 409
    assert upload(client).status_code == 409
    assert client.get(endpoint).content == VIDEO


def test_paths_cannot_escape_data_root(client, database):
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        storage_path("../outside.mp4")
    source = upload(client).json()
    with Session(database[0]) as session:
        file = session.scalar(select(MediaFile))
        file.local_path = "../outside.mp4"
        session.commit()
    assert client.get(f'/api/assets/{source["assets"][0]["id"]}/content').status_code == 409


def test_concurrent_imports_have_one_source_and_blob(client, database):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: upload(client), range(2)))
    assert sorted(r.status_code for r in results) == [201, 409]
    with Session(database[0]) as session:
        assert session.scalar(select(func.count()).select_from(Source)) == 1
        assert session.scalar(select(func.count()).select_from(MediaFile)) == 1


def test_attach_rejects_stale_version_and_trash(client):
    source = save(client)
    edited = client.patch(f'/api/sources/{source["id"]}', json={**version(source), "title": "Nuevo"}).json()
    assert upload(client, source=source).status_code == 409
    trashed = client.request("DELETE", f'/api/sources/{source["id"]}', json=version(edited)).json()
    assert upload(client, source=trashed).status_code == 409


def test_organization_normalization_search_combined_filters_and_clear(client, database):
    source = save(client)
    other = save(client, "other")
    edited = organize(client, source, ["  Edición  de   vídeo ", "edición de vídeo", "CAFÉ"], ["Aprender"]).json()
    assert len(edited["tags"]) == 2
    assert organize(client, source, ["stale"]).status_code == 409
    second = organize(client, other, ["café"]).json()
    assert next(t["id"] for t in edited["tags"] if t["name"] == "CAFÉ") == second["tags"][0]["id"]
    category = edited["categories"][0]["id"]
    found = client.get("/api/sources", params={"q": "vídeo", "category": category, "source_type": "url", "platform": "other"}).json()
    assert found["total"] == 1 and found["items"][0]["id"] == source["id"]
    assert client.get("/api/sources?q=%25").json()["total"] == 0
    assert client.get("/api/sources?source_type=file").json()["total"] == 0
    database[0].dispose()
    assert client.get(f'/api/sources/{source["id"]}').json()["tags"] == edited["tags"]
    cleared = organize(client, edited).json()
    assert cleared["tags"] == cleared["categories"] == []


def test_concurrent_organization_reuses_labels(client):
    sources = [save(client, "a"), save(client, "b")]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda source: organize(client, source, ["Uno", "Dos"], ["Común"]), sources))
    assert [r.status_code for r in results] == [200, 200]
    assert len(client.get("/api/organization").json()["tags"]) == 2


@pytest.mark.parametrize("tags", [[""], ["a" * 61], [str(n) for n in range(21)]])
def test_invalid_labels_do_not_change_source(client, tags):
    source = save(client)
    assert organize(client, source, tags).status_code == 422
    assert client.get(f'/api/sources/{source["id"]}').json() == source


def test_queue_cancel_requeue_trash_restore_and_persistence(client, database):
    first, second = save(client, "a"), save(client, "b")
    assert [s["id"] for s in client.get("/api/sources?view=queue").json()["items"]] == [first["id"], second["id"]]
    endpoint = f'/api/sources/{first["id"]}/queue'
    cancelled = client.put(endpoint, json={**version(first), "queued": False}).json()
    assert client.get("/api/sources?view=queue").json()["total"] == 1
    assert client.put(endpoint, json={**version(first), "queued": True}).status_code == 409
    queued = client.put(endpoint, json={**version(cancelled), "queued": True}).json()
    assert [s["id"] for s in client.get("/api/sources?view=queue").json()["items"]] == [second["id"], first["id"]]
    trashed = client.request("DELETE", f'/api/sources/{first["id"]}', json=version(queued)).json()
    assert client.get("/api/sources?view=queue").json()["total"] == 1
    client.post(f'/api/sources/{first["id"]}/restore', json=version(trashed))
    database[0].dispose()
    assert client.get("/api/sources?view=queue").json()["total"] == 2
    assert client.get("/api/health").json()["processing"]["state"] == "stopped"
    assert client.post("/api/processing/start").status_code == 404


@pytest.mark.parametrize("database", ["0001_sources"], indirect=True)
def test_upgrade_populated_schema_preserves_sources_and_backfills_queue(database):
    engine, config = database
    with engine.begin() as connection:
        source_id = connection.scalar(text("INSERT INTO sources(platform, source_type, original_url, title) VALUES ('other', 'url', 'https://example.com/old', 'Conservar') RETURNING id"))
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        command.check(config)
    with Session(engine) as session:
        assert session.get(Source, source_id).title == "Conservar"
        assert session.scalar(select(func.count()).select_from(ProcessingJob)) == 1
        with pytest.raises(IntegrityError):
            session.add(ProcessingJob(source_id=source_id, status="running"))
            session.commit()
