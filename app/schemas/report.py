from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StudentReportItem(BaseModel):
    student_id: int
    student_code: str
    full_name: str
    email: str
    phone: str | None
    course_id: int | None
    course_name: str | None
    status: str
    date_of_birth: date | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceReportItem(BaseModel):
    student_id: int
    student_code: str
    student_name: str
    course_name: str | None
    total_marked_days: int
    present_days: int
    absent_days: int
    late_days: int
    attendance_percentage: float

    model_config = ConfigDict(from_attributes=True)


class DetailedAttendanceItem(BaseModel):
    date: date | None
    student_code: str
    student_name: str
    course_name: str | None
    status: str
    remarks: str | None
    marked_by: int

    model_config = ConfigDict(from_attributes=True)


class FeeReportItem(BaseModel):
    student_id: int
    student_code: str
    student_name: str
    course_name: str | None
    title: str
    total_amount: Decimal
    paid_amount: Decimal
    balance: Decimal
    due_date: date
    status: str

    model_config = ConfigDict(from_attributes=True)


class CourseReportItem(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    is_active: bool
    student_count: int
    active_student_count: int
    average_attendance_percentage: float | None
    total_fees_assigned: Decimal
    total_fees_collected: Decimal
    total_fees_pending: Decimal

    model_config = ConfigDict(from_attributes=True)


class ReportFilters(BaseModel):
    search: str | None = None
    course_id: int | None = None
    status: str | None = None
    student_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    created_from: date | None = None
    created_to: date | None = None
    due_from: date | None = None
    due_to: date | None = None
    detail: bool = False
    page: int = 1
    page_size: int = 100
