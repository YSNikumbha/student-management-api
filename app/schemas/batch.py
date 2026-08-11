from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class BatchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    course_id: int
    academic_year_id: int
    semester_id: int | None = None
    section: str | None = Field(None, max_length=10)
    capacity: int | None = Field(None, gt=0)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        return value.strip()


class BatchCreate(BatchBase):
    is_active: bool = True


class BatchUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    course_id: int | None = None
    academic_year_id: int | None = None
    semester_id: int | None = None
    section: str | None = Field(None, max_length=10)
    capacity: int | None = Field(None, gt=0)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if value is not None:
            return value.strip()
        return value


class BatchResponse(BatchBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}