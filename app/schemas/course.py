from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    duration_months: int | None = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    duration_months: int | None = None
    is_active: bool | None = None


class CourseResponse(CourseBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
