from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.course import Course
    from app.models.fee_structure import FeeStructure
    from app.models.student import Student
    from app.models.subject import Subject
    from app.models.batch import Batch


class Semester(Base):
    __tablename__ = "semesters"
    __table_args__ = (
        UniqueConstraint("academic_year_id", "course_id", "number", name="uq_semester_year_course_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    academic_year_id: Mapped[int] = mapped_column(
        ForeignKey("academic_years.id"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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

    academic_year: Mapped[AcademicYear] = relationship(back_populates="semesters")
    course: Mapped[Course] = relationship(back_populates="semesters")
    subjects: Mapped[list[Subject]] = relationship(back_populates="semester", cascade="all, delete-orphan")
    batches: Mapped[list[Batch]] = relationship(back_populates="semester", cascade="all, delete-orphan")
    students: Mapped[list[Student]] = relationship(back_populates="semester")
    attendance_sessions: Mapped[list["AttendanceSession"]] = relationship(back_populates="semester")
    fee_structures: Mapped[list[FeeStructure]] = relationship(back_populates="semester")
