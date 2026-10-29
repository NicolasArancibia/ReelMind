from uuid import uuid4

import pytest
from alembic import command
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_session
from app.main import app
from app.models import Source


def test_save_commits_and_is_visible_from_a_new_connection(client, database):
    response = client.post("/api/sources", json={"url": "https://www.youtube.com/watch?v=demo", "title": "Mi idea"})
    assert response.status_code == 201
    saved = response.json()
    assert saved["platform"] == "youtube"
    assert saved["status"] == "pending"
    assert saved["title"] == "Mi idea"
    assert saved["created_at"]
    with Session(database[0]) as session:
        source = session.scalar(select(Source).where(Source.id == saved["id"]))
        assert source is not None and source.title == "Mi idea"
    assert client.get(f'/api/sources/{saved["id"]}').json() == saved
    assert client.get("/api/sources").json()["total"] == 1


def test_duplicate_rolls_back_and_next_request_still_works(client):
    payload = {"url": "https://www.instagram.com/reel/demo/?utm_source=personal"}
    assert client.post("/api/sources", json=payload).status_code == 201
    assert client.post("/api/sources", json=payload).status_code == 409
    assert client.get("/api/sources").json()["total"] == 1
    # Do not strip query parameters: their semantics have not been verified.
    other = {"url": "https://www.instagram.com/reel/demo/?utm_source=other"}
    assert client.post("/api/sources", json=other).status_code == 201
    assert client.get("/api/sources").json()["total"] == 2


@pytest.mark.parametrize("payload", [
    {"url": "not-a-url"}, {"url": "javascript:alert(1)"},
    {"url": "ftp://example.com/video"}, {"url": "https://user:secret@example.com/video"},
    {"url": "https://example.com", "title": "a" * 241},
    {"url": "https://example.com", "status": "completed"}, {"url": " "},
])
def test_invalid_input_is_not_saved_or_reflected(client, payload):
    response = client.post("/api/sources", json=payload)
    assert response.status_code == 422
    assert "secret" not in response.text
    assert client.get("/api/sources").json()["total"] == 0


def test_domain_matching_does_not_trust_lookalike_hosts(client):
    result = client.post("/api/sources", json={"url": "https://youtube.com.evil.example/video"}).json()
    assert result["platform"] == "other"


def test_health_never_starts_processing(client):
    for _ in range(2):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["processing"] == {
            "state": "stopped", "available": False, "autostart": False, "concurrency": 1,
        }
    assert client.post("/api/processing/start").status_code == 404


def test_reapplying_migration_preserves_records(client, database):
    saved = client.post("/api/sources", json={"url": "https://example.com/persist"}).json()
    engine, config = database
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    assert client.get(f'/api/sources/{saved["id"]}').status_code == 200


def test_external_origin_and_host_are_rejected(client):
    payload = {"url": "https://example.com"}
    assert client.post("/api/sources", json=payload, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.get("/api/sources", headers={"Host": "evil.example"}).status_code == 400
    assert client.get("/api/sources").json()["total"] == 0


def test_db_error_is_clear_and_does_not_leak_credentials(client):
    def broken_session():
        raise SQLAlchemyError("password=should-never-appear")
        yield
    app.dependency_overrides[get_session] = broken_session
    response = client.get("/api/health")
    assert response.status_code == 503
    assert "should-never-appear" not in response.text


def test_health_requires_expected_migration(client, database):
    with database[0].begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num = 'unexpected'"))
    assert client.get("/api/health").status_code == 503


def test_missing_and_bounded_queries(client):
    assert client.get(f"/api/sources/{uuid4()}").status_code == 404
    assert client.get("/api/sources?limit=0").status_code == 422
    assert client.get("/api/sources?limit=101").status_code == 422


@pytest.mark.parametrize("overrides", [
    {"REELMIND_PROCESSING_AUTOSTART": True}, {"REELMIND_MAX_HEAVY_TASKS": 2},
    {"PGHOST": "external.example"},
])
def test_unsafe_configuration_fails_closed(overrides):
    with pytest.raises(ValidationError) as error:
        Settings(PGPASSWORD="test-not-a-real-secret", **overrides)
    assert "test-not-a-real-secret" not in str(error.value)
