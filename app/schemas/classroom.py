from datetime import datetime

from pydantic import BaseModel, Field


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    course_id: int
    academic_year_id: int
    semester_id: int | None = None
    class_teacher_id: int | None = None
    section: str | None = Field(default=None, max_length=10)
    capacity: int | None = Field(default=None, gt=0)
    room: str | None = Field(default=None, max_length=50)
    schedule: str | None = Field(default=None, max_length=150)
    is_active: bool = True


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    course_id: int | None = None
    academic_year_id: int | None = None
    semester_id: int | None = None
    class_teacher_id: int | None = None
    section: str | None = Field(default=None, max_length=10)
    capacity: int | None = Field(default=None, gt=0)
    room: str | None = Field(default=None, max_length=50)
    schedule: str | None = Field(default=None, max_length=150)
    is_active: bool | None = None


class ClassResponse(BaseModel):
    id: int
    name: str
    program: str | None = None
    grade: str | None = None
    section: str | None = None
    teacher: str | None = None
    class_teacher_id: int | None = None
    student_count: int
    average_gpa: float
    room: str | None = None
    schedule: str | None = None
    course_id: int
    academic_year_id: int
    semester_id: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
