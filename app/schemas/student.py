from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class StudentBase(BaseModel):
    student_code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None
    course_id: int | None = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    student_code: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    course_id: int | None = None
    status: str | None = None


class StudentResponse(StudentBase):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
