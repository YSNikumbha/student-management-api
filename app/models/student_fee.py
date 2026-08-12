from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.fee_installment import FeeInstallment
    from app.models.fee_structure import FeeStructure
    from app.models.payment import Payment
    from app.models.student import Student
    from app.models.user import User


class StudentFee(Base):
    __tablename__ = "student_fees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
        index=True,
    )
    fee_structure_id: Mapped[int | None] = mapped_column(
        ForeignKey("fee_structures.id"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    student: Mapped[Student] = relationship(back_populates="fees")
    fee_structure: Mapped[FeeStructure | None] = relationship(back_populates="student_fees")
    installments: Mapped[list[FeeInstallment]] = relationship(
        back_populates="student_fee",
        passive_deletes=True,
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="student_fee",
        passive_deletes=True,
    )
    creator: Mapped[User] = relationship(back_populates="created_fees")
