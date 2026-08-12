from datetime import date as date_type, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssessmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    subject_id: int
    semester_id: int
    academic_year_id: int
    assessment_type: str = Field(min_length=2, max_length=50)
    max_marks: Decimal = Field(gt=Decimal("0.00"), max_digits=7, decimal_places=2)
    weight_percentage: Decimal | None = Field(default=None, gt=Decimal("0.00"), le=Decimal("100.00"))
    date: date_type | None = None

    @field_validator("name", "assessment_type")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class AssessmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    assessment_type: str | None = Field(default=None, min_length=2, max_length=50)
    max_marks: Decimal | None = Field(default=None, gt=Decimal("0.00"), max_digits=7, decimal_places=2)
    weight_percentage: Decimal | None = Field(default=None, gt=Decimal("0.00"), le=Decimal("100.00"))
    date: date_type | None = None


class AssessmentResponse(BaseModel):
    id: int
    name: str
    subject_id: int
    semester_id: int
    academic_year_id: int
    assessment_type: str
    max_marks: Decimal
    weight_percentage: Decimal | None = None
    date: date_type | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentResultCreate(BaseModel):
    student_id: int
    marks_obtained: Decimal = Field(ge=Decimal("0.00"), max_digits=7, decimal_places=2)
    remarks: str | None = Field(default=None, max_length=500)


class StudentResultResponse(BaseModel):
    id: int
    assessment_id: int
    student_id: int
    marks_obtained: Decimal
    grade: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BulkStudentResultRequest(BaseModel):
    results: list[StudentResultCreate]


class StudentAcademicSummaryResponse(BaseModel):
    student_id: int
    percentage: float
    gpa: float
    grade: str
    assessments_count: int
