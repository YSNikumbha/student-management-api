from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InstallmentStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class FeeCategoryCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2 or len(normalized) > 100:
            raise ValueError("Category name must be between 2 and 100 characters.")
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        return value.strip()


class FeeCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) < 2 or len(normalized) > 100:
            raise ValueError("Category name must be between 2 and 100 characters.")
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        return value.strip()


class FeeCategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class FeeStructureCreate(BaseModel):
    name: str = Field(max_length=150)
    course_id: int
    academic_year_id: int
    semester_id: int | None = None
    category_id: int
    total_amount: Decimal = Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3 or len(normalized) > 150:
            raise ValueError("Fee structure name must be between 3 and 150 characters.")
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        return value.strip()


class FeeStructureUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    course_id: int | None = None
    academic_year_id: int | None = None
    semester_id: int | None = None
    category_id: int | None = None
    total_amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
    )
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) < 3 or len(normalized) > 150:
            raise ValueError("Fee structure name must be between 3 and 150 characters.")
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        return value.strip()


class FeeStructureResponse(BaseModel):
    id: int
    name: str
    course_id: int
    course_name: str | None = None
    academic_year_id: int
    academic_year_name: str | None = None
    semester_id: int | None
    semester_name: str | None = None
    category_id: int
    category_name: str | None = None
    total_amount: Decimal
    description: str | None
    is_active: bool
    created_at: datetime
    assignment_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class FeeInstallmentCreate(BaseModel):
    title: str = Field(max_length=150)
    amount: Decimal = Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)
    due_date: date
    sequence_number: int = Field(ge=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2 or len(normalized) > 150:
            raise ValueError("Installment title must be between 2 and 150 characters.")
        return normalized


class FeeInstallmentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=150)
    amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
    )
    due_date: date | None = None
    sequence_number: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) < 2 or len(normalized) > 150:
            raise ValueError("Installment title must be between 2 and 150 characters.")
        return normalized


class FeeInstallmentResponse(BaseModel):
    id: int
    student_fee_id: int
    title: str
    amount: Decimal
    due_date: date
    sequence_number: int
    paid_amount: Decimal
    balance: Decimal
    status: InstallmentStatus

    model_config = ConfigDict(from_attributes=True)


class FeeStructureAssignRequest(BaseModel):
    student_id: int | None = None
    batch_id: int | None = None
    due_date: date
    installments: list[FeeInstallmentCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_target(self) -> "FeeStructureAssignRequest":
        has_student = self.student_id is not None
        has_batch = self.batch_id is not None
        if has_student == has_batch:
            raise ValueError("Provide exactly one of student_id or batch_id.")
        return self


class FeeStructureAssignResponse(BaseModel):
    created: int
    skipped: int
    student_fee_ids: list[int]
