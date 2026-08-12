from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.notification import Notification, NotificationType
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.user import User
from app.schemas.pagination import get_offset

FEE_NOTIFICATION_ROLES = {"admin", "accountant", "staff"}
ATTENDANCE_NOTIFICATION_ROLES = {"admin", "teacher", "staff"}
ZERO_MONEY = Decimal("0.00")


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType | str = NotificationType.info,
    dedupe_unread: bool = True,
) -> Notification:
    notification_type_value = str(getattr(notification_type, "value", notification_type))
    if dedupe_unread:
        existing = db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.title == title,
                Notification.message == message,
                Notification.type == notification_type_value,
                Notification.is_read.is_(False),
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    notification = Notification(
        user_id=user_id,
        title=title[:150],
        message=message[:1000],
        type=notification_type_value,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def safely_create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType | str = NotificationType.info,
    dedupe_unread: bool = True,
) -> Notification | None:
    try:
        return create_notification(
            db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            dedupe_unread=dedupe_unread,
        )
    except Exception:
        db.rollback()
        return None


def notify_account_created(db: Session, user: User) -> Notification | None:
    return safely_create_notification(
        db,
        user_id=user.id,
        title="Account created",
        message="Your account has been created. Please sign in with the temporary password shared by an administrator.",
        notification_type=NotificationType.system,
    )


def notify_password_reset(db: Session, user: User) -> Notification | None:
    return safely_create_notification(
        db,
        user_id=user.id,
        title="Password reset",
        message="An administrator reset your password. Please use the new temporary password.",
        notification_type=NotificationType.system,
    )


def get_notifications_paginated(
    db: Session,
    *,
    user_id: int,
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[Notification], int]:
    statement = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))

    total_items = db.execute(
        select(func.count()).select_from(statement.with_only_columns(Notification.id).subquery())
    ).scalar_one()

    statement = (
        statement.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )
    return list(db.execute(statement).scalars().all()), total_items


def get_unread_count(db: Session, *, user_id: int) -> int:
    return db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    ).scalar_one()


def get_user_notification(
    db: Session,
    *,
    user_id: int,
    notification_id: int,
) -> Notification | None:
    return db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    ).scalar_one_or_none()


def mark_notification_read(db: Session, notification: Notification) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        db.add(notification)
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_read(db: Session, *, user_id: int) -> int:
    notifications = db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    ).scalars().all()
    now = datetime.now(UTC)
    for notification in notifications:
        notification.is_read = True
        notification.read_at = now
    db.commit()
    return len(notifications)


def generate_user_notifications(db: Session, user: User) -> None:
    if user.role in FEE_NOTIFICATION_ROLES:
        _generate_fee_notifications(db, user)
    if user.role in ATTENDANCE_NOTIFICATION_ROLES:
        _generate_low_attendance_notification(db, user)


def _payment_totals_subquery():
    return (
        select(
            Payment.student_fee_id,
            func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
        )
        .group_by(Payment.student_fee_id)
        .subquery()
    )


def _fee_counts(db: Session) -> tuple[int, int]:
    today = date.today()
    due_soon_end = today + timedelta(days=7)
    payment_totals = _payment_totals_subquery()
    paid_amount = func.coalesce(payment_totals.c.paid_amount, 0)
    balance = StudentFee.total_amount - paid_amount
    statement = (
        select(StudentFee.due_date, balance)
        .outerjoin(payment_totals, StudentFee.id == payment_totals.c.student_fee_id)
        .where(balance > 0)
    )

    overdue_count = 0
    due_soon_count = 0
    for due_date, _balance in db.execute(statement).all():
        if due_date < today:
            overdue_count += 1
        elif today <= due_date <= due_soon_end:
            due_soon_count += 1

    return overdue_count, due_soon_count


def _generate_fee_notifications(db: Session, user: User) -> None:
    overdue_count, due_soon_count = _fee_counts(db)
    if overdue_count:
        safely_create_notification(
            db,
            user_id=user.id,
            title="Fees overdue",
            message=f"{overdue_count} student fee record{' is' if overdue_count == 1 else 's are'} overdue.",
            notification_type=NotificationType.fee_due,
        )
    if due_soon_count:
        safely_create_notification(
            db,
            user_id=user.id,
            title="Fees due soon",
            message=f"{due_soon_count} student fee record{' is' if due_soon_count == 1 else 's are'} due in the next 7 days.",
            notification_type=NotificationType.fee_due,
        )


def _low_attendance_count(db: Session) -> int:
    total = func.count(Attendance.id)
    present = func.sum(case((Attendance.status == "present", 1), else_=0))
    statement = (
        select(Student.id, total.label("total_sessions"), present.label("present_sessions"))
        .join(Attendance, Attendance.student_id == Student.id)
        .group_by(Student.id)
    )

    count = 0
    for _student_id, total_sessions, present_sessions in db.execute(statement).all():
        total_sessions = total_sessions or 0
        if total_sessions == 0:
            continue
        percentage = ((present_sessions or 0) / total_sessions) * 100
        if percentage < 75:
            count += 1
    return count


def _generate_low_attendance_notification(db: Session, user: User) -> None:
    low_count = _low_attendance_count(db)
    if not low_count:
        return
    safely_create_notification(
        db,
        user_id=user.id,
        title="Low attendance",
        message=f"{low_count} student{' is' if low_count == 1 else 's are'} below the 75% attendance threshold.",
        notification_type=NotificationType.attendance_warning,
    )
