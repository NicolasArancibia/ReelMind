from functools import lru_cache
from pathlib import Path
import os

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    pg_host: str = Field(default="127.0.0.1", validation_alias="PGHOST")
    pg_port: int = Field(default=5432, validation_alias="PGPORT", ge=1, le=65535)
    pg_database: str = Field(default="reelmind", validation_alias="PGDATABASE")
    pg_user: str = Field(default="reelmind_app", validation_alias="PGUSER")
    pg_password: SecretStr = Field(validation_alias="PGPASSWORD")
    processing_autostart: bool = Field(
        default=False, validation_alias="REELMIND_PROCESSING_AUTOSTART"
    )
    max_heavy_tasks: int = Field(default=1, validation_alias="REELMIND_MAX_HEAVY_TASKS")
    data_root: Path = Field(default_factory=lambda: Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local")) / "ReelMind" / "data", validation_alias="REELMIND_DATA_ROOT")
    max_upload_bytes: int = Field(default=2 * 1024**3, ge=1, validation_alias="REELMIND_MAX_UPLOAD_BYTES")

    @model_validator(mode="after")
    def local_manual_only(self):
        if not self.data_root.is_absolute():
            raise ValueError("La raíz de datos debe ser absoluta.")
        if self.pg_host not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("La base debe ser local en esta fase.")
        if self.processing_autostart or self.max_heavy_tasks != 1:
            raise ValueError("El procesamiento debe permanecer manual y secuencial.")
        return self

    @property
    def database_url(self) -> URL:
        # URL.create safely encodes symbols without interpolating a password into text.
        return URL.create(
            "postgresql+psycopg",
            username=self.pg_user,
            password=self.pg_password.get_secret_value(),
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_database,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
