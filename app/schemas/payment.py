from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)
    payment_date: date
    payment_method: PaymentMethod
    reference_number: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=500)


class PaymentResponse(BaseModel):
    id: int
    student_fee_id: int
    amount: Decimal
    payment_date: date
    payment_method: PaymentMethod
    reference_number: str | None
    notes: str | None
    recorded_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
