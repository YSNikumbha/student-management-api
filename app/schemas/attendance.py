from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.attendance import AttendanceStatus


class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: AttendanceStatus
    remarks: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, value: date) -> date:
        """Validate that attendance date is not in the future."""
        today = date.today()
        if value > today:
            raise ValueError("Attendance date cannot be in the future.")
        return value

    @field_validator("remarks")
    @classmethod
    def validate_remarks(cls, value: str | None) -> str | None:
        """Validate and normalize remarks."""
        if value is None or value.strip() == "":
            return None
        normalized = value.strip()
        if len(normalized) > 500:
            raise ValueError("Remarks must be 500 characters or less.")
        return normalized


class AttendanceBulkItem(BaseModel):
    student_id: int
    status: AttendanceStatus
    remarks: str | None = None

    @field_validator("remarks")
    @classmethod
    def validate_remarks(cls, value: str | None) -> str | None:
        """Validate and normalize remarks."""
        if value is None or value.strip() == "":
            return None
        normalized = value.strip()
        if len(normalized) > 500:
            raise ValueError("Remarks must be 500 characters or less.")
        return normalized


class AttendanceBulkCreate(BaseModel):
    date: date
    records: list[AttendanceBulkItem] = Field(min_length=1)

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, value: date) -> date:
        """Validate that attendance date is not in the future."""
        today = date.today()
        if value > today:
            raise ValueError("Attendance date cannot be in the future.")
        return value


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None
    remarks: str | None = None

    @field_validator("remarks")
    @classmethod
    def validate_remarks(cls, value: str | None) -> str | None:
        """Validate and normalize remarks."""
        if value is None or value.strip() == "":
            return None
        normalized = value.strip()
        if len(normalized) > 500:
            raise ValueError("Remarks must be 500 characters or less.")
        return normalized


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
