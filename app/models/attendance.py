from datetime import UTC, date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AttendanceStatus(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"
    excused = "excused"


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "date",
            name="uq_attendances_student_id_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    attendance_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("attendance_sessions.id"),
        nullable=True,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    remarks: Mapped[str | None] = mapped_column(String(500), nullable=True)
    marked_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
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

    session: Mapped["AttendanceSession"] = relationship(back_populates="attendance_records")
    student: Mapped["Student"] = relationship(back_populates="attendances")
    marked_by_user: Mapped["User"] = relationship(back_populates="attendances_marked")
