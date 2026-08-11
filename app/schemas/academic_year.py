from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel, Field, field_validator


class AcademicYearBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates(cls, value: date) -> date:
        return value


class AcademicYearCreate(AcademicYearBase):
    is_active: bool = True

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        return end_date


class AcademicYearUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
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


class AcademicYearResponse(AcademicYearBase):
    id: int
    is_active: bool
    semesters: List[dict] = []

    model_config = {"from_attributes": True}