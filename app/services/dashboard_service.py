from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.schemas.dashboard import (
    AttendanceTodayStats,
    CourseDashboardStats,
    CourseStatResponse,
    DashboardSummaryResponse,
    FeeDashboardStats,
    RecentActivityResponse,
    RecentAttendanceItem,
    RecentPaymentItem,
    RecentStudentItem,
    StudentDashboardStats,
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
