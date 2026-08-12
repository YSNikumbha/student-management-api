from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.semester import Semester
    from app.models.student import Student
    from app.models.subject import Subject


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_months: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    students: Mapped[list[Student]] = relationship(back_populates="course")
    semesters: Mapped[list[Semester]] = relationship(back_populates="course", cascade="all, delete-orphan")
    subjects: Mapped[list[Subject]] = relationship(back_populates="course", cascade="all, delete-orphan")
    batches: Mapped[list[Batch]] = relationship(back_populates="course", cascade="all, delete-orphan")
    attendance_sessions: Mapped[list["AttendanceSession"]] = relationship(back_populates="course")
