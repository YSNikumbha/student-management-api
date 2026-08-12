from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.course import Course
    from app.models.fee_category import FeeCategory
    from app.models.semester import Semester
    from app.models.student_fee import StudentFee


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    academic_year_id: Mapped[int] = mapped_column(
        ForeignKey("academic_years.id"),
        nullable=False,
        index=True,
    )
    semester_id: Mapped[int | None] = mapped_column(
        ForeignKey("semesters.id"),
        nullable=True,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("fee_categories.id"),
        nullable=False,
        index=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    course: Mapped[Course] = relationship(back_populates="fee_structures")
    academic_year: Mapped[AcademicYear] = relationship(back_populates="fee_structures")
    semester: Mapped[Semester | None] = relationship(back_populates="fee_structures")
    category: Mapped[FeeCategory] = relationship(back_populates="fee_structures")
    student_fees: Mapped[list[StudentFee]] = relationship(back_populates="fee_structure")
