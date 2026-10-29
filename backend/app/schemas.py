from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator

url_adapter = TypeAdapter(HttpUrl)


class SourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    url: str = Field(min_length=1, max_length=4096)
    title: str | None = Field(default=None, max_length=240)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = url_adapter.validate_python(value)
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("El enlace no puede contener credenciales.")
        return value

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        return value or None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    platform: str
    original_url: str
    title: str | None
    status: str
    created_at: datetime


class SourcePage(BaseModel):
    items: list[SourceRead]
    total: int
