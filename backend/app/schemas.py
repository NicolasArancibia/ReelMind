from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator

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


class SourceMutation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_updated_at: AwareDatetime


class SourceUpdate(SourceMutation):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(max_length=240)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        return value or None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    platform: str
    original_url: str | None
    source_type: str
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    tags: list["LabelRead"] = []
    categories: list["LabelRead"] = []
    assets: list["AssetRead"] = []
    job: "JobRead | None" = None


class SourcePage(BaseModel):
    items: list[SourceRead]
    total: int
    active_total: int
    trash_total: int
    offset: int
    limit: int
    queue_total: int = 0


class LabelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    checksum: str
    mime_type: str
    size_bytes: int


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    original_name: str
    file: FileRead


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    created_at: datetime


class OrganizationUpdate(SourceMutation):
    tags: list[str] = Field(max_length=20)
    categories: list[str] = Field(max_length=10)

    @field_validator("tags", "categories")
    @classmethod
    def clean_names(cls, names):
        import unicodedata
        result = {}
        for value in names:
            name = " ".join(unicodedata.normalize("NFC", value).split())
            if not name or len(name) > 60 or any(ord(c) < 32 for c in name):
                raise ValueError("Cada nombre debe tener entre 1 y 60 caracteres.")
            result.setdefault(name.casefold(), name)
        return list(result.values())


class QueueUpdate(SourceMutation):
    queued: bool


SourceRead.model_rebuild()
