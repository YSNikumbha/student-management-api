from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession
from app.models.batch import Batch
from app.models.course import Course
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.subject import Subject
from app.schemas.dashboard import (
    AttentionFeeItem,
    AttendanceTodayStats,
    CourseDashboardStats,
    CourseStatResponse,
    DashboardAttentionResponse,
    DashboardSummaryResponse,
    FeeDashboardStats,
    LowAttendanceStudentItem,
    RecentActivityResponse,
    RecentAdmittedStudentItem,
    RecentAttendanceItem,
    RecentPaymentItem,
    RecentStudentItem,
    StudentDashboardStats,
    UnmarkedSessionItem,
)
from app.services import fee_service


def _count(db: Session, statement) -> int:
    return db.execute(statement).scalar_one()


def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    today = date.today()

    total_students = _count(db, select(func.count()).select_from(Student))
    active_students = _count(
        db,
        select(func.count()).select_from(Student).where(Student.status == "active"),
    )
    inactive_students = _count(
        db,
        select(func.count()).select_from(Student).where(Student.status == "inactive"),
    )

    total_courses = _count(db, select(func.count()).select_from(Course))
    active_courses = _count(
        db,
        select(func.count()).select_from(Course).where(Course.is_active.is_(True)),
    )

    marked_today = _count(
        db,
        select(func.count()).select_from(Attendance).where(Attendance.date == today),
    )
    present_today = _count(
        db,
        select(func.count())
        .select_from(Attendance)
        .where(Attendance.date == today, Attendance.status == "present"),
    )
    absent_today = _count(
        db,
        select(func.count())
        .select_from(Attendance)
        .where(Attendance.date == today, Attendance.status == "absent"),
    )
    late_today = _count(
        db,
        select(func.count())
        .select_from(Attendance)
        .where(Attendance.date == today, Attendance.status == "late"),
    )

    fee_summary = fee_service.get_fee_summary(db)

    return DashboardSummaryResponse(
        students=StudentDashboardStats(
            total=total_students,
            active=active_students,
            inactive=inactive_students,
        ),
        courses=CourseDashboardStats(
            total=total_courses,
            active=active_courses,
        ),
        attendance_today=AttendanceTodayStats(
            marked=marked_today,
            present=present_today,
            absent=absent_today,
            late=late_today,
        ),
        fees=FeeDashboardStats(
            total_assigned=fee_summary["total_assigned"],
            total_collected=fee_summary["total_collected"],
            total_pending=fee_summary["total_pending"],
            overdue_count=fee_summary["overdue_count"],
        ),
    )


def get_recent_activity(db: Session) -> RecentActivityResponse:
    student_statement = (
        select(Student)
        .order_by(Student.id.desc())
        .limit(5)
    )
    recent_students = [
        RecentStudentItem(
            id=student.id,
            student_code=student.student_code,
            name=f"{student.first_name} {student.last_name}",
            email=student.email,
            course_id=student.course_id,
            status=student.status,
            created_at=student.created_at,
        )
        for student in db.execute(student_statement).scalars().all()
    ]

    payment_statement = (
        select(Payment, StudentFee, Student)
        .join(StudentFee, Payment.student_fee_id == StudentFee.id)
        .join(Student, StudentFee.student_id == Student.id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .limit(5)
    )
    recent_payments = [
        RecentPaymentItem(
            id=payment.id,
            fee_id=fee.id,
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            fee_title=fee.title,
            amount=payment.amount,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            created_at=payment.created_at,
        )
        for payment, fee, student in db.execute(payment_statement).all()
    ]

    attendance_statement = (
        select(Attendance, Student)
        .join(Student, Attendance.student_id == Student.id)
        .order_by(Attendance.updated_at.desc(), Attendance.id.desc())
        .limit(5)
    )
    recent_attendance = [
        RecentAttendanceItem(
            id=attendance.id,
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            date=attendance.date,
            status=attendance.status,
            updated_at=attendance.updated_at,
        )
        for attendance, student in db.execute(attendance_statement).all()
    ]

    return RecentActivityResponse(
        recent_students=recent_students,
        recent_payments=recent_payments,
        recent_attendance=recent_attendance,
    )


def get_course_stats(db: Session) -> list[CourseStatResponse]:
    statement = (
        select(
            Course.id,
            Course.code,
            Course.name,
            func.count(Student.id),
        )
        .outerjoin(Student, Student.course_id == Course.id)
        .group_by(Course.id, Course.code, Course.name)
        .order_by(Course.name.asc())
    )

    return [
        CourseStatResponse(
            course_id=course_id,
            course_code=course_code,
            course_name=course_name,
            student_count=student_count,
        )
        for course_id, course_code, course_name, student_count in db.execute(statement).all()
    ]


def get_dashboard_attention(db: Session) -> DashboardAttentionResponse:
    return DashboardAttentionResponse(
        low_attendance_students=_get_low_attendance_students(db),
        overdue_fees=_get_outstanding_fee_items(db, status="overdue"),
        fees_due_soon=_get_outstanding_fee_items(db, status="due_soon"),
        unmarked_attendance_sessions_today=_get_unmarked_sessions_today(db),
        recently_admitted_students=_get_recently_admitted_students(db),
        recent_payments=_get_recent_payment_items(db),
    )


def _get_low_attendance_students(db: Session, limit: int = 10) -> list[LowAttendanceStudentItem]:
    total = func.count(Attendance.id)
    present = func.sum(case((Attendance.status == "present", 1), else_=0))
    statement = (
        select(
            Student.id,
            Student.student_code,
            Student.first_name,
            Student.last_name,
            total.label("total_sessions"),
            present.label("present_sessions"),
        )
        .join(Attendance, Attendance.student_id == Student.id)
        .group_by(Student.id, Student.student_code, Student.first_name, Student.last_name)
    )

    items: list[LowAttendanceStudentItem] = []
    for student_id, student_code, first_name, last_name, total_sessions, present_sessions in db.execute(statement).all():
        total_sessions = total_sessions or 0
        if total_sessions == 0:
            continue
        percentage = round(((present_sessions or 0) / total_sessions) * 100, 2)
        if percentage < 75:
            items.append(
                LowAttendanceStudentItem(
                    student_id=student_id,
                    student_code=student_code,
                    student_name=f"{first_name} {last_name}",
                    attendance_percentage=percentage,
                    total_sessions=total_sessions,
                    url=f"/admin/attendance?student_id={student_id}",
                )
            )

    return sorted(items, key=lambda item: (item.attendance_percentage, item.student_name))[:limit]


def _payment_totals_subquery():
    return (
        select(
            Payment.student_fee_id,
            func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
        )
        .group_by(Payment.student_fee_id)
        .subquery()
    )


def _get_outstanding_fee_items(
    db: Session,
    *,
    status: str,
    limit: int = 10,
) -> list[AttentionFeeItem]:
    today = date.today()
    due_soon_end = today + timedelta(days=7)
    payment_totals = _payment_totals_subquery()
    paid_amount = func.coalesce(payment_totals.c.paid_amount, 0)
    balance = (StudentFee.total_amount - paid_amount).label("balance")
    statement = (
        select(StudentFee, Student, balance)
        .join(Student, StudentFee.student_id == Student.id)
        .outerjoin(payment_totals, StudentFee.id == payment_totals.c.student_fee_id)
        .where(balance > 0)
    )

    if status == "overdue":
        statement = statement.where(StudentFee.due_date < today)
    else:
        statement = statement.where(
            StudentFee.due_date >= today,
            StudentFee.due_date <= due_soon_end,
        )

    statement = statement.order_by(StudentFee.due_date.asc(), StudentFee.id.asc()).limit(limit)
    return [
        AttentionFeeItem(
            fee_id=fee.id,
            student_id=student.id,
            student_code=student.student_code,
            student_name=f"{student.first_name} {student.last_name}",
            title=fee.title,
            due_date=fee.due_date,
            balance=fee_service.normalize_money(Decimal(str(item_balance))),
            url="/admin/fees?status=overdue" if status == "overdue" else "/admin/fees",
        )
        for fee, student, item_balance in db.execute(statement).all()
    ]


def _get_unmarked_sessions_today(db: Session, limit: int = 10) -> list[UnmarkedSessionItem]:
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    attendance_count = func.count(Attendance.id)
    statement = (
        select(
            AttendanceSession,
            Subject.name,
            Batch.name,
            attendance_count.label("record_count"),
        )
        .join(Subject, AttendanceSession.subject_id == Subject.id)
        .join(Batch, AttendanceSession.batch_id == Batch.id)
        .outerjoin(Attendance, Attendance.attendance_session_id == AttendanceSession.id)
        .where(
            AttendanceSession.date >= start,
            AttendanceSession.date <= end,
        )
        .group_by(AttendanceSession.id, Subject.name, Batch.name)
        .having(attendance_count == 0)
        .order_by(AttendanceSession.date.asc(), AttendanceSession.id.asc())
        .limit(limit)
    )
    return [
        UnmarkedSessionItem(
            session_id=session.id,
            session_name=session.session_name,
            date=session.date,
            subject_name=subject_name,
            batch_name=batch_name,
            url=f"/admin/attendance?session_id={session.id}",
        )
        for session, subject_name, batch_name, _record_count in db.execute(statement).all()
    ]


def _get_recently_admitted_students(db: Session, limit: int = 10) -> list[RecentAdmittedStudentItem]:
    statement = (
        select(Student)
        .order_by(Student.admission_date.desc(), Student.created_at.desc(), Student.id.desc())
        .limit(limit)
    )
    return [
        RecentAdmittedStudentItem(
            student_id=student.id,
            student_code=student.student_code,
            student_name=f"{student.first_name} {student.last_name}",
            admission_date=student.admission_date,
            created_at=student.created_at,
            url=f"/admin/students?search={student.student_code}",
        )
        for student in db.execute(statement).scalars().all()
    ]


def _get_recent_payment_items(db: Session, limit: int = 10) -> list[RecentPaymentItem]:
    statement = (
        select(Payment, StudentFee, Student)
        .join(StudentFee, Payment.student_fee_id == StudentFee.id)
        .join(Student, StudentFee.student_id == Student.id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .limit(limit)
    )
    return [
        RecentPaymentItem(
            id=payment.id,
            fee_id=fee.id,
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            fee_title=fee.title,
            amount=payment.amount,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            created_at=payment.created_at,
        )
        for payment, fee, student in db.execute(statement).all()
    ]
