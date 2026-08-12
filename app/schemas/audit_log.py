from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    user_name: str | None = None
    user_email: str | None = None
    action: str
    entity_type: str
    entity_id: str | None
    description: str
    metadata_json: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogFilters(BaseModel):
    user_id: int | None = Field(default=None, alias="user")
    action: str | None = None
    entity_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    search: str | None = None

    @field_validator("action", "entity_type", "search")
    @classmethod
    def strip_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
