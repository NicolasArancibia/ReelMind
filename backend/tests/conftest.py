from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.main import app


@pytest.fixture
def database():
    """Each test migrates an isolated, randomly named schema in local PostgreSQL.

    Never clear public tables or replace the user's database.
    """
    schema = "reelmind_test_" + uuid4().hex
    admin_engine = create_engine(get_settings().database_url, hide_parameters=True)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        get_settings().database_url, hide_parameters=True,
        connect_args={"options": f"-csearch_path={schema}", "connect_timeout": 5},
    )
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine, config
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


@pytest.fixture
def client(database):
    engine, _ = database

    def isolated_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = isolated_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
