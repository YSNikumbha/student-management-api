from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.attendance import AttendanceStatus
from app.models.payment import PaymentMethod


class StudentDashboardStats(BaseModel):
    total: int
    active: int
    inactive: int


class CourseDashboardStats(BaseModel):
    total: int
    active: int


class AttendanceTodayStats(BaseModel):
    marked: int
    present: int
    absent: int
    late: int


class FeeDashboardStats(BaseModel):
    total_assigned: Decimal
    total_collected: Decimal
    total_pending: Decimal
    overdue_count: int


class DashboardSummaryResponse(BaseModel):
    students: StudentDashboardStats
    courses: CourseDashboardStats
    attendance_today: AttendanceTodayStats
    fees: FeeDashboardStats


class RecentStudentItem(BaseModel):
    id: int
    student_code: str
    name: str
    email: str
    course_id: int | None
    status: str
    created_at: datetime


class RecentPaymentItem(BaseModel):
    id: int
    fee_id: int
    student_id: int
    student_name: str
    fee_title: str
    amount: Decimal
    payment_date: date
    payment_method: PaymentMethod
    created_at: datetime


class RecentAttendanceItem(BaseModel):
    id: int
    student_id: int
    student_name: str
    date: date
    status: AttendanceStatus
    updated_at: datetime


class RecentActivityResponse(BaseModel):
    recent_students: list[RecentStudentItem]
    recent_payments: list[RecentPaymentItem]
    recent_attendance: list[RecentAttendanceItem]


class CourseStatResponse(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    student_count: int
