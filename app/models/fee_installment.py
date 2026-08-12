from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.student_fee import StudentFee


class FeeInstallment(Base):
    __tablename__ = "fee_installments"
    __table_args__ = (
        UniqueConstraint("student_fee_id", "sequence_number", name="uq_fee_installment_fee_sequence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_fee_id: Mapped[int] = mapped_column(
        ForeignKey("student_fees.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    student_fee: Mapped[StudentFee] = relationship(back_populates="installments")
    payments: Mapped[list[Payment]] = relationship(back_populates="fee_installment")
