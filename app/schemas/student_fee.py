from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.payment import PaymentResponse
from app.schemas.fee_structure import FeeInstallmentResponse


class FeeStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class StudentFeeCreate(BaseModel):
    student_id: int
    invoice_number: str | None = Field(default=None, max_length=50)
    title: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=500)
    total_amount: Decimal = Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)
    due_date: date

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        """Validate and normalize title."""
        if not value or not value.strip():
            raise ValueError("Fee title is required.")
        normalized = value.strip()
        if len(normalized) < 3 or len(normalized) > 150:
            raise ValueError("Fee title must be between 3 and 150 characters.")
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        """Validate and normalize description."""
        if value is None or value.strip() == "":
            return None
        normalized = value.strip()
        if len(normalized) > 500:
            raise ValueError("Description must be 500 characters or less.")
        return normalized


class StudentFeeUpdate(BaseModel):
    invoice_number: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    total_amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
    )
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        """Validate and normalize title."""
        if value is None:
            return None
        if not value or not value.strip():
            raise ValueError("Fee title is required.")
        normalized = value.strip()
        if len(normalized) < 3 or len(normalized) > 150:
            raise ValueError("Fee title must be between 3 and 150 characters.")
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        """Validate and normalize description."""
        if value is None or value.strip() == "":
            return None
        normalized = value.strip()
        if len(normalized) > 500:
            raise ValueError("Description must be 500 characters or less.")
        return normalized


class StudentFeeResponse(BaseModel):
    id: int
    student_id: int
    fee_structure_id: int | None = None
    invoice_number: str | None = None
    fee_structure_name: str | None = None
    student_code: str | None = None
    student_name: str | None = None
    course_id: int | None = None
    title: str
    description: str | None
    total_amount: Decimal
    paid_amount: Decimal
    balance: Decimal
    due_date: date
    status: FeeStatus
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentFeeDetailResponse(StudentFeeResponse):
    payments: list[PaymentResponse]
    installments: list[FeeInstallmentResponse] = Field(default_factory=list)


class FeeSummaryResponse(BaseModel):
    total_assigned: Decimal
    total_collected: Decimal
    total_pending: Decimal
    unpaid_count: int
    partial_count: int
    paid_count: int
    overdue_count: int
