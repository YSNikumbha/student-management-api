from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.payment import PaymentResponse


class FeeStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class StudentFeeCreate(BaseModel):
    student_id: int
    title: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=500)
    total_amount: Decimal = Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)
    due_date: date


class StudentFeeUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    total_amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
    )
    due_date: date | None = None


class StudentFeeResponse(BaseModel):
    id: int
    student_id: int
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


class FeeSummaryResponse(BaseModel):
    total_assigned: Decimal
    total_collected: Decimal
    total_pending: Decimal
    unpaid_count: int
    partial_count: int
    paid_count: int
    overdue_count: int
