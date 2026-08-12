from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.batch import Batch
    from app.models.course import Course
    from app.models.semester import Semester
    from app.models.student import Student
    from app.models.subject import Subject
    from app.models.user import User

    # Import Course for relationship type hints
    Course = Course


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"),
        nullable=False,
        index=True,
    )
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semesters.id"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    session_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
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

    course: Mapped["Course"] = relationship(back_populates="attendance_sessions")
    batch: Mapped["Batch"] = relationship(back_populates="attendance_sessions")
    semester: Mapped["Semester"] = relationship(back_populates="attendance_sessions")
    subject: Mapped["Subject"] = relationship(back_populates="attendance_sessions")
    created_by_user: Mapped["User"] = relationship(back_populates="attendance_sessions")
    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
