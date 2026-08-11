from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.batch import Batch
    from app.models.course import Course
    from app.models.semester import Semester
    from app.models.student_fee import StudentFee


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id"),
        nullable=True,
    )
    academic_year_id: Mapped[int | None] = mapped_column(
        ForeignKey("academic_years.id"),
        nullable=True,
        index=True,
    )
    semester_id: Mapped[int | None] = mapped_column(
        ForeignKey("semesters.id"),
        nullable=True,
        index=True,
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("batches.id"),
        nullable=True,
        index=True,
    )
    admission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    course: Mapped[Course | None] = relationship(back_populates="students")
    academic_year: Mapped[AcademicYear | None] = relationship(back_populates="students")
    semester: Mapped[Semester | None] = relationship(back_populates="students")
    batch: Mapped[Batch | None] = relationship(back_populates="students")
    fees: Mapped[list[StudentFee]] = relationship(
        back_populates="student",
        passive_deletes=True,
    )
