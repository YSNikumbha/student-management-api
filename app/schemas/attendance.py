from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance import AttendanceStatus


class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: AttendanceStatus
    remarks: str | None = Field(default=None, max_length=500)


class AttendanceBulkItem(BaseModel):
    student_id: int
    status: AttendanceStatus
    remarks: str | None = Field(default=None, max_length=500)


class AttendanceBulkCreate(BaseModel):
    date: date
    records: list[AttendanceBulkItem] = Field(min_length=1)


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None
    remarks: str | None = Field(default=None, max_length=500)


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    date: date
    status: AttendanceStatus
    remarks: str | None
    marked_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceBulkResponse(BaseModel):
    date: date
    created: int
    updated: int
    records: list[AttendanceResponse]


class CourseAttendanceStudent(BaseModel):
    student_id: int
    student_code: str
    name: str
    attendance_id: int | None = None
    status: AttendanceStatus | None = None
    remarks: str | None = None


class CourseAttendanceResponse(BaseModel):
    course_id: int
    date: date
    students: list[CourseAttendanceStudent]


class StudentAttendanceSummary(BaseModel):
    student_id: int
    total_marked_days: int
    present_days: int
    absent_days: int
    late_days: int
    attendance_percentage: float
