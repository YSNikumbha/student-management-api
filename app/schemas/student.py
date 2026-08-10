from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class StudentBase(BaseModel):
    student_code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
