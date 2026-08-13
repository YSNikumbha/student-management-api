from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_role_name(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    normalized = "_".join(part for part in normalized.split("_") if part)
    if len(normalized) < 2 or len(normalized) > 50:
        raise ValueError("Role name must be between 2 and 50 characters")
    if not all(character.isalnum() or character == "_" for character in normalized):
        raise ValueError("Role name can contain only letters, numbers, spaces, hyphens, and underscores")
    return normalized


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    module: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    display_name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _normalize_role_name(value)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 2 or len(trimmed) > 100:
            raise ValueError("Display name must be between 2 and 100 characters")
        return trimmed

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class RoleCreate(RoleBase):
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_role_name(value)

    @field_validator("display_name")
    @classmethod
    def validate_optional_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if len(trimmed) < 2 or len(trimmed) > 100:
            raise ValueError("Display name must be between 2 and 100 characters")
        return trimmed

    @field_validator("description")
    @classmethod
    def normalize_optional_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class RolePermissionUpdate(BaseModel):
    permission_codes: list[str] = Field(default_factory=list)


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None = None
    is_system: bool
    is_active: bool
    user_count: int = 0
    permission_codes: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleListResponse(BaseModel):
    roles: list[RoleResponse]
    permissions: list[PermissionResponse]
