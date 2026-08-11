from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SubjectBase(BaseModel):
    course_id: int
    semester_id: int
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=3, max_length=150)
    description: str | None = None
    credits: int | None = Field(None, gt=0)

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class SubjectCreate(SubjectBase):
    is_active: bool = True


class SubjectUpdate(BaseModel):
    course_id: int | None = None
    semester_id: int | None = None
    code: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=3, max_length=150)
    description: str | None = None
    credits: int | None = Field(None, gt=0)
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str | None) -> str | None:
        if value is not None:
            return value.strip().upper()
        return value


class SubjectResponse(SubjectBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}