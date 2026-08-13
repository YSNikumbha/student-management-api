from __future__ import annotations

import calendar
from datetime import date as Date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReportPeriod(str, Enum):
    daily = "daily"
    monthly = "monthly"
    yearly = "yearly"
    custom = "custom"


class ReportFilter(BaseModel):
    period: ReportPeriod | None = None
    date: Date | None = None
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=1900, le=2200)
    from_date: Date | None = None
    to_date: Date | None = None
    class_id: int | None = None
    student_id: int | None = None
    start_date: Date | None = None
    end_date: Date | None = None

    def effective_range(self) -> tuple[Date | None, Date | None]:
        if self.period is None:
            return self.start_date, self.end_date
        if self.period == ReportPeriod.daily:
            return self.date, self.date
        if self.period == ReportPeriod.monthly and self.year is not None and self.month is not None:
            last_day = calendar.monthrange(self.year, self.month)[1]
            return Date(self.year, self.month, 1), Date(self.year, self.month, last_day)
        if self.period == ReportPeriod.yearly and self.year is not None:
            return Date(self.year, 1, 1), Date(self.year, 12, 31)
        if self.period == ReportPeriod.custom:
            return self.from_date, self.to_date
        return None, None

    @property
    def active_period(self) -> str:
        return self.period.value if self.period else "all"


class StudentReportItem(BaseModel):
    student_id: int
    student_code: str
    full_name: str
    email: str
    phone: str | None
    course_id: int | None
    course_name: str | None
    status: str
    date_of_birth: Date | None
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
    excused_days: int = 0
    attendance_percentage: float

    model_config = ConfigDict(from_attributes=True)


class DetailedAttendanceItem(BaseModel):
    date: Date | None
    student_id: int
    student_code: str
    student_name: str
    course_name: str | None
    status: str
    remarks: str | None
    marked_by: int

    model_config = ConfigDict(from_attributes=True)


class FeeReportItem(BaseModel):
    fee_id: int
    student_id: int
    student_code: str
    student_name: str
    course_name: str | None
    title: str
    fee_category: str | None = None
    total_amount: Decimal
    paid_amount: Decimal
    balance: Decimal
    due_date: Date
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
    start_date: Date | None = None
    end_date: Date | None = None
    created_from: Date | None = None
    created_to: Date | None = None
    due_from: Date | None = None
    due_to: Date | None = None
    detail: bool = False
    page: int = 1
    page_size: int = 100


class AttendanceReportSummary(BaseModel):
    present: int
    absent: int
    late: int
    excused: int
    total: int
    attendance_percentage: float


class FinancialReportSummary(BaseModel):
    total_billed: Decimal
    collected: Decimal
    outstanding: Decimal
    collection_rate: float
    paid_count: int
    partial_count: int
    overdue_count: int
    date_basis: str
