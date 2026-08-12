from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.semester import Semester
    from app.models.student import Student
    from app.models.subject import Subject


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    academic_year_id: Mapped[int] = mapped_column(
        ForeignKey("academic_years.id"),
        nullable=False,
        index=True,
    )
    assessment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    weight_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
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

    subject: Mapped["Subject"] = relationship(back_populates="assessments")
    semester: Mapped["Semester"] = relationship(back_populates="assessments")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="assessments")
    results: Mapped[list["StudentResult"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class StudentResult(Base):
    __tablename__ = "student_results"
    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", name="uq_student_result_assessment_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    assessment: Mapped[Assessment] = relationship(back_populates="results")
    student: Mapped["Student"] = relationship(back_populates="results")
