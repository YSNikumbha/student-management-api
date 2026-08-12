from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.attendance import Attendance
    from app.models.attendance_session import AttendanceSession
    from app.models.batch import Batch
    from app.models.notification import Notification
    from app.models.payment import Payment
    from app.models.student_document import StudentDocument
    from app.models.student_fee import StudentFee


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="staff")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_fees: Mapped[list[StudentFee]] = relationship(
        back_populates="creator",
        passive_deletes=True,
    )
    recorded_payments: Mapped[list[Payment]] = relationship(
        back_populates="recorder",
        passive_deletes=True,
    )
    student_documents_uploaded: Mapped[list[StudentDocument]] = relationship(
        back_populates="uploader",
        passive_deletes=True,
    )
    attendances_marked: Mapped[list[Attendance]] = relationship(back_populates="marked_by_user")
    attendance_sessions: Mapped[list[AttendanceSession]] = relationship(back_populates="created_by_user")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="user")
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )
    classes_taught: Mapped[list[Batch]] = relationship(
        back_populates="class_teacher",
        passive_deletes=True,
    )
