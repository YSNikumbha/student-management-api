from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.payment import PaymentMethod


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)
    payment_date: date
    payment_method: PaymentMethod
    reference_number: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("payment_date")
    @classmethod
    def validate_payment_date_not_future(cls, value: date) -> date:
        """Validate that payment date is not in the future."""
        today = date.today()
        if value > today:
            raise ValueError("Payment date cannot be in the future.")
        return value

    @field_validator("reference_number")
    @classmethod
    def validate_reference_number(cls, value: str | None) -> str | None:
        """Validate and normalize reference number."""
        if value is None or value.strip() == "":
            return None
        normalized = value.strip()
        if len(normalized) > 150:
            raise ValueError("Reference number must be 150 characters or less.")
        return normalized

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        """Validate and normalize notes."""
        if value is None or value.strip() == "":
            return None
        normalized = value.strip()
        if len(normalized) > 500:
            raise ValueError("Notes must be 500 characters or less.")
        return normalized


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
