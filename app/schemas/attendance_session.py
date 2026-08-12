from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class AttendanceSessionBase(BaseModel):
    course_id: int
    batch_id: int
    semester_id: int
    subject_id: int
    session_name: str | None = Field(None, max_length=100)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, end_time: datetime | None, info) -> datetime | None:
        if end_time is None:
            return end_time
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class AttendanceSessionCreate(AttendanceSessionBase):
    date: datetime

    @field_validator("date")
    @classmethod
    def validate_not_future(cls, value: datetime) -> datetime:
        from datetime import datetime as dt
        now = dt.now()
        if value > now:
            raise ValueError("Session date cannot be in the future")
        return value


class AttendanceSessionUpdate(BaseModel):
    course_id: int | None = None
    batch_id: int | None = None
    semester_id: int | None = None
    subject_id: int | None = None
    session_name: str | None = Field(None, max_length=100)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, end_time: datetime | None, info) -> datetime | None:
        if end_time is None:
            return end_time
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class AttendanceSessionResponse(AttendanceSessionBase):
    id: int
    date: datetime
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AttendanceSessionWithDetails(AttendanceSessionResponse):
    course_name: str | None = None
    batch_name: str | None = None
    semester_name: str | None = None
    subject_name: str | None = None
    subject_code: str | None = None
    created_by_name: str | None = None
    student_count: int = 0

    model_config = {"from_attributes": True}


class AttendanceRecordBulk(BaseModel):
    student_id: int
    status: str = Field(..., pattern="^(present|absent|late|excused)$")
    remarks: str | None = Field(None, max_length=500)


class AttendanceBulkCreate(BaseModel):
    records: List[AttendanceRecordBulk]