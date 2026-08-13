from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SemesterBase(BaseModel):
    academic_year_id: int
    course_id: int
    number: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        return value.strip()


class SemesterCreate(SemesterBase):
    is_active: bool = True

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date | None, info) -> date | None:
        if end_date is None:
            return end_date
        start_date = info.data.get("start_date")
        if start_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        return end_date


class SemesterUpdate(BaseModel):
    academic_year_id: int | None = None
    course_id: int | None = None
    number: int | None = Field(None, gt=0)
    name: str | None = Field(None, min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if value is not None:
            return value.strip()
        return value

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date | None, info) -> date | None:
        if end_date is None:
            return end_date
        start_date = info.data.get("start_date")
        if start_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        return end_date


class SemesterSubjectSummary(BaseModel):
    id: int
    course_id: int
    semester_id: int
    code: str
    name: str
    description: str | None = None
    credits: int | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SemesterBatchSummary(BaseModel):
    id: int
    name: str
    course_id: int
    academic_year_id: int
    semester_id: int | None = None
    class_teacher_id: int | None = None
    section: str | None = None
    capacity: int | None = None
    room: str | None = None
    schedule: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SemesterResponse(SemesterBase):
    id: int
    is_active: bool
    subjects: list[SemesterSubjectSummary] = Field(default_factory=list)
    batches: list[SemesterBatchSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
