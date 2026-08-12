from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.course import Course
    from app.models.semester import Semester
    from app.models.student import Student
    from app.models.user import User


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )
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
    class_teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    section: Mapped[str | None] = mapped_column(String(10), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    room: Mapped[str | None] = mapped_column(String(50), nullable=True)
    schedule: Mapped[str | None] = mapped_column(String(150), nullable=True)
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

    course: Mapped[Course] = relationship(back_populates="batches")
    academic_year: Mapped[AcademicYear] = relationship(back_populates="batches")
    semester: Mapped[Semester | None] = relationship(back_populates="batches")
    class_teacher: Mapped[User | None] = relationship(back_populates="classes_taught")
    students: Mapped[list[Student]] = relationship(back_populates="batch")
    attendance_sessions: Mapped[list["AttendanceSession"]] = relationship(back_populates="batch")
