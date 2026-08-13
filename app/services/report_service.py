from datetime import date, datetime
from io import StringIO
from typing import Literal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.academic_performance import Assessment, StudentResult
from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession
from app.models.batch import Batch
from app.models.course import Course
from app.models.fee_category import FeeCategory
from app.models.fee_structure import FeeStructure
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.subject import Subject
from app.models.user import User
from app.schemas.report import (
    AttendanceReportItem,
    AttendanceReportSummary,
    CourseReportItem,
    DetailedAttendanceItem,
    FeeReportItem,
    FinancialReportSummary,
    StudentReportItem,
)


def _attendance_effective_date():
    return func.coalesce(Attendance.date, func.date(AttendanceSession.date))


def _attendance_course_id():
    return func.coalesce(Student.course_id, AttendanceSession.course_id)


def _attendance_class_id():
    return func.coalesce(Student.batch_id, AttendanceSession.batch_id)


def _student_name_expression():
    return Student.first_name + " " + Student.last_name


def _fee_status_expression(paid_amount):
    balance = StudentFee.total_amount - paid_amount
    return case(
        (balance <= 0, "paid"),
        (StudentFee.due_date < date.today(), "overdue"),
        (paid_amount > 0, "partial"),
        else_="unpaid",
    )


def get_student_report(
    db: Session,
    *,
    search: str | None = None,
    course_id: int | None = None,
    status: str | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[StudentReportItem], int]:
    statement = select(
        Student.id,
        Student.student_code,
        (Student.first_name + " " + Student.last_name).label("full_name"),
        Student.email,
        Student.phone,
        Student.course_id,
        Course.name.label("course_name"),
        Student.status,
        Student.date_of_birth,
        Student.created_at,
    ).outerjoin(Course, Student.course_id == Course.id)

    if search:
        search_pattern = f"%{search.lower()}%"
        statement = statement.where(
            or_(
                func.lower(Student.student_code).like(search_pattern),
                func.lower(Student.first_name).like(search_pattern),
                func.lower(Student.last_name).like(search_pattern),
                func.lower(Student.email).like(search_pattern),
            ),
        )

    if course_id is not None:
        statement = statement.where(Student.course_id == course_id)

    if status is not None:
        statement = statement.where(Student.status == status)

    if created_from is not None:
        statement = statement.where(Student.created_at >= created_from)

    if created_to is not None:
        statement = statement.where(Student.created_at <= created_to)

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    statement = (
        statement.order_by(Student.created_at.desc(), Student.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = db.execute(statement).all()
    items = [
        StudentReportItem(
            student_id=row.id,
            student_code=row.student_code,
            full_name=row.full_name,
            email=row.email,
            phone=row.phone,
            course_id=row.course_id,
            course_name=row.course_name,
            status=row.status,
            date_of_birth=row.date_of_birth,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return items, total_items


def get_attendance_report(
    db: Session,
    *,
    course_id: int | None = None,
    class_id: int | None = None,
    student_id: int | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    detail: bool = False,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[AttendanceReportItem | DetailedAttendanceItem], int]:
    attendance_date = _attendance_effective_date()
    attendance_course_id = _attendance_course_id()
    attendance_class_id = _attendance_class_id()

    if detail:
        statement = (
            select(
                attendance_date.label("date"),
                Student.id.label("student_id"),
                Student.student_code,
                _student_name_expression().label("student_name"),
                func.coalesce(Batch.name, Course.name).label("course_name"),
                Attendance.status,
                Attendance.remarks,
                Attendance.marked_by,
            )
            .join(Student, Attendance.student_id == Student.id)
            .outerjoin(
                AttendanceSession,
                Attendance.attendance_session_id == AttendanceSession.id,
            )
            .outerjoin(Batch, Batch.id == attendance_class_id)
            .outerjoin(Course, Course.id == attendance_course_id)
        )

        if course_id is not None:
            statement = statement.where(attendance_course_id == course_id)

        if class_id is not None:
            statement = statement.where(attendance_class_id == class_id)

        if student_id is not None:
            statement = statement.where(Attendance.student_id == student_id)

        if status is not None:
            statement = statement.where(Attendance.status == status)

        if start_date is not None:
            statement = statement.where(attendance_date >= start_date)

        if end_date is not None:
            statement = statement.where(attendance_date <= end_date)

        count_statement = select(func.count()).select_from(
            statement.order_by(None).subquery(),
        )
        total_items = db.execute(count_statement).scalar_one()

        statement = (
            statement.order_by(attendance_date.desc(), Student.student_code)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        rows = db.execute(statement).all()
        items = [
            DetailedAttendanceItem(
                date=row.date,
                student_id=row.student_id,
                student_code=row.student_code,
                student_name=row.student_name,
                course_name=row.course_name,
                status=row.status,
                remarks=row.remarks,
                marked_by=row.marked_by,
            )
            for row in rows
        ]
        return items, total_items

    student_ids_subquery = (
        select(Attendance.student_id)
        .select_from(Attendance)
        .join(Student, Attendance.student_id == Student.id)
        .outerjoin(
            AttendanceSession,
            Attendance.attendance_session_id == AttendanceSession.id,
        )
        .outerjoin(Course, Course.id == attendance_course_id)
    )

    if course_id is not None:
        student_ids_subquery = student_ids_subquery.where(attendance_course_id == course_id)

    if class_id is not None:
        student_ids_subquery = student_ids_subquery.where(attendance_class_id == class_id)

    if student_id is not None:
        student_ids_subquery = student_ids_subquery.where(Attendance.student_id == student_id)

    if status is not None:
        student_ids_subquery = student_ids_subquery.where(Attendance.status == status)

    if start_date is not None:
        student_ids_subquery = student_ids_subquery.where(attendance_date >= start_date)

    if end_date is not None:
        student_ids_subquery = student_ids_subquery.where(attendance_date <= end_date)

    distinct_student_ids = student_ids_subquery.distinct().subquery()

    summary_subquery = (
        select(
            Attendance.student_id,
            func.count().label("total_marked_days"),
            func.sum(case((Attendance.status == "present", 1), else_=0)).label("present_days"),
            func.sum(case((Attendance.status == "absent", 1), else_=0)).label("absent_days"),
            func.sum(case((Attendance.status == "late", 1), else_=0)).label("late_days"),
            func.sum(case((Attendance.status == "excused", 1), else_=0)).label("excused_days"),
        )
        .join(Student, Attendance.student_id == Student.id)
        .outerjoin(
            AttendanceSession,
            Attendance.attendance_session_id == AttendanceSession.id,
        )
        .outerjoin(Course, Course.id == attendance_course_id)
        .group_by(Attendance.student_id)
    )

    if course_id is not None:
        summary_subquery = summary_subquery.where(attendance_course_id == course_id)

    if class_id is not None:
        summary_subquery = summary_subquery.where(attendance_class_id == class_id)

    if student_id is not None:
        summary_subquery = summary_subquery.where(Attendance.student_id == student_id)

    if status is not None:
        summary_subquery = summary_subquery.where(Attendance.status == status)

    if start_date is not None:
        summary_subquery = summary_subquery.where(attendance_date >= start_date)

    if end_date is not None:
        summary_subquery = summary_subquery.where(attendance_date <= end_date)

    summary = summary_subquery.subquery()

    statement = (
        select(
            summary.c.student_id,
            Student.student_code,
            _student_name_expression().label("student_name"),
            func.coalesce(Batch.name, Course.name).label("course_name"),
            summary.c.total_marked_days,
            summary.c.present_days,
            summary.c.absent_days,
            summary.c.late_days,
            summary.c.excused_days,
        )
        .join(Student, summary.c.student_id == Student.id)
        .outerjoin(Batch, Student.batch_id == Batch.id)
        .outerjoin(Course, Student.course_id == Course.id)
    )

    count_statement = select(func.count()).select_from(distinct_student_ids)
    total_items = db.execute(count_statement).scalar_one()

    statement = (
        statement.order_by(Student.student_code)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = db.execute(statement).all()
    items = []
    for row in rows:
        total = row.total_marked_days or 0
        percentage = (
            round((row.present_days or 0) / total * 100, 2)
            if total
            else 0.0
        )
        items.append(
            AttendanceReportItem(
                student_id=row.student_id,
                student_code=row.student_code,
                student_name=row.student_name,
                course_name=row.course_name,
                total_marked_days=total,
                present_days=row.present_days or 0,
                absent_days=row.absent_days or 0,
                late_days=row.late_days or 0,
                excused_days=row.excused_days or 0,
                attendance_percentage=percentage,
            )
        )
    return items, total_items


def get_attendance_summary(
    db: Session,
    *,
    course_id: int | None = None,
    class_id: int | None = None,
    student_id: int | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AttendanceReportSummary:
    attendance_date = _attendance_effective_date()
    attendance_course_id = _attendance_course_id()
    attendance_class_id = _attendance_class_id()
    statement = (
        select(
            func.sum(case((Attendance.status == "present", 1), else_=0)).label("present"),
            func.sum(case((Attendance.status == "absent", 1), else_=0)).label("absent"),
            func.sum(case((Attendance.status == "late", 1), else_=0)).label("late"),
            func.sum(case((Attendance.status == "excused", 1), else_=0)).label("excused"),
            func.count(Attendance.id).label("total"),
        )
        .join(Student, Attendance.student_id == Student.id)
        .outerjoin(AttendanceSession, Attendance.attendance_session_id == AttendanceSession.id)
    )
    if course_id is not None:
        statement = statement.where(attendance_course_id == course_id)
    if class_id is not None:
        statement = statement.where(attendance_class_id == class_id)
    if student_id is not None:
        statement = statement.where(Attendance.student_id == student_id)
    if status is not None:
        statement = statement.where(Attendance.status == status)
    if start_date is not None:
        statement = statement.where(attendance_date >= start_date)
    if end_date is not None:
        statement = statement.where(attendance_date <= end_date)

    row = db.execute(statement).one()
    present = int(row.present or 0)
    absent = int(row.absent or 0)
    late = int(row.late or 0)
    excused = int(row.excused or 0)
    total = int(row.total or 0)
    return AttendanceReportSummary(
        present=present,
        absent=absent,
        late=late,
        excused=excused,
        total=total,
        attendance_percentage=round((present / total) * 100, 2) if total else 0.0,
    )


def get_fee_report(
    db: Session,
    *,
    student_id: int | None = None,
    course_id: int | None = None,
    class_id: int | None = None,
    category_id: int | None = None,
    status: str | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[FeeReportItem], int]:
    payment_totals = (
        select(
            Payment.student_fee_id,
            func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
        )
        .group_by(Payment.student_fee_id)
        .subquery()
    )

    paid_amount = func.coalesce(payment_totals.c.paid_amount, 0)
    balance = StudentFee.total_amount - paid_amount
    fee_status = _fee_status_expression(paid_amount)

    statement = (
        select(
            StudentFee.id,
            StudentFee.student_id,
            Student.student_code,
            _student_name_expression().label("student_name"),
            func.coalesce(Batch.name, Course.name).label("course_name"),
            StudentFee.title,
            FeeCategory.name.label("fee_category"),
            StudentFee.total_amount,
            paid_amount.label("paid_amount"),
            balance.label("balance"),
            StudentFee.due_date,
            fee_status.label("fee_status"),
        )
        .outerjoin(payment_totals, StudentFee.id == payment_totals.c.student_fee_id)
        .join(Student, StudentFee.student_id == Student.id)
        .outerjoin(Batch, Student.batch_id == Batch.id)
        .outerjoin(Course, Student.course_id == Course.id)
        .outerjoin(FeeStructure, StudentFee.fee_structure_id == FeeStructure.id)
        .outerjoin(FeeCategory, FeeStructure.category_id == FeeCategory.id)
    )

    if student_id is not None:
        statement = statement.where(StudentFee.student_id == student_id)

    if course_id is not None:
        statement = statement.where(Student.course_id == course_id)

    if class_id is not None:
        statement = statement.where(Student.batch_id == class_id)

    if category_id is not None:
        statement = statement.where(FeeCategory.id == category_id)

    if due_from is not None:
        statement = statement.where(StudentFee.due_date >= due_from)

    if due_to is not None:
        statement = statement.where(StudentFee.due_date <= due_to)

    if status is not None:
        statement = statement.where(fee_status == status)

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    statement = (
        statement.order_by(StudentFee.due_date.desc(), StudentFee.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = db.execute(statement).all()
    items = []
    for row in rows:
        items.append(
            FeeReportItem(
                fee_id=row.id,
                student_id=row.student_id,
                student_code=row.student_code,
                student_name=row.student_name,
                course_name=row.course_name,
                title=row.title,
                fee_category=row.fee_category,
                total_amount=row.total_amount,
                paid_amount=row.paid_amount,
                balance=row.balance,
                due_date=row.due_date,
                status=row.fee_status,
            )
        )
    return items, total_items


def get_financial_summary(
    db: Session,
    *,
    student_id: int | None = None,
    course_id: int | None = None,
    class_id: int | None = None,
    category_id: int | None = None,
    status: str | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    payment_from: date | None = None,
    payment_to: date | None = None,
) -> FinancialReportSummary:
    payment_totals = (
        select(
            Payment.student_fee_id,
            func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
        )
        .group_by(Payment.student_fee_id)
        .subquery()
    )
    paid_amount = func.coalesce(payment_totals.c.paid_amount, 0)
    balance = StudentFee.total_amount - paid_amount
    fee_status = _fee_status_expression(paid_amount)
    fee_statement = (
        select(
            StudentFee.id,
            StudentFee.total_amount,
            balance.label("balance"),
            fee_status.label("fee_status"),
        )
        .outerjoin(payment_totals, StudentFee.id == payment_totals.c.student_fee_id)
        .join(Student, StudentFee.student_id == Student.id)
        .outerjoin(FeeStructure, StudentFee.fee_structure_id == FeeStructure.id)
        .outerjoin(FeeCategory, FeeStructure.category_id == FeeCategory.id)
    )
    if student_id is not None:
        fee_statement = fee_statement.where(StudentFee.student_id == student_id)
    if course_id is not None:
        fee_statement = fee_statement.where(Student.course_id == course_id)
    if class_id is not None:
        fee_statement = fee_statement.where(Student.batch_id == class_id)
    if category_id is not None:
        fee_statement = fee_statement.where(FeeCategory.id == category_id)
    if due_from is not None:
        fee_statement = fee_statement.where(StudentFee.due_date >= due_from)
    if due_to is not None:
        fee_statement = fee_statement.where(StudentFee.due_date <= due_to)
    if status is not None:
        fee_statement = fee_statement.where(fee_status == status)

    fee_rows = db.execute(fee_statement).all()
    total_billed = sum((row.total_amount for row in fee_rows), start=0)
    outstanding = sum((row.balance for row in fee_rows), start=0)
    paid_count = sum(1 for row in fee_rows if row.fee_status == "paid")
    partial_count = sum(1 for row in fee_rows if row.fee_status == "partial")
    overdue_count = sum(1 for row in fee_rows if row.fee_status == "overdue")

    payment_statement = (
        select(func.coalesce(func.sum(Payment.amount), 0))
        .join(StudentFee, Payment.student_fee_id == StudentFee.id)
        .join(Student, StudentFee.student_id == Student.id)
        .outerjoin(FeeStructure, StudentFee.fee_structure_id == FeeStructure.id)
        .outerjoin(FeeCategory, FeeStructure.category_id == FeeCategory.id)
    )
    if student_id is not None:
        payment_statement = payment_statement.where(StudentFee.student_id == student_id)
    if course_id is not None:
        payment_statement = payment_statement.where(Student.course_id == course_id)
    if class_id is not None:
        payment_statement = payment_statement.where(Student.batch_id == class_id)
    if category_id is not None:
        payment_statement = payment_statement.where(FeeCategory.id == category_id)
    if payment_from is not None:
        payment_statement = payment_statement.where(Payment.payment_date >= payment_from)
    if payment_to is not None:
        payment_statement = payment_statement.where(Payment.payment_date <= payment_to)

    collected = db.execute(payment_statement).scalar_one()
    collection_rate = round((float(collected) / float(total_billed)) * 100, 2) if total_billed else 0.0
    return FinancialReportSummary(
        total_billed=total_billed,
        collected=collected,
        outstanding=outstanding,
        collection_rate=collection_rate,
        paid_count=paid_count,
        partial_count=partial_count,
        overdue_count=overdue_count,
        date_basis="Billed/outstanding use fee due_date; collected uses payment_date.",
    )


def get_course_report(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[CourseReportItem], int]:
    statement = select(Course)

    if search:
        search_pattern = f"%{search.lower()}%"
        statement = statement.where(
            or_(
                func.lower(Course.code).like(search_pattern),
                func.lower(Course.name).like(search_pattern),
            ),
        )

    if is_active is not None:
        statement = statement.where(Course.is_active == is_active)

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    statement = (
        statement.order_by(Course.code)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    courses = db.execute(statement).scalars().all()
    items = []
    for course in courses:
        student_count = db.execute(
            select(func.count()).select_from(Student).where(Student.course_id == course.id)
        ).scalar_one()

        active_student_count = db.execute(
            select(func.count())
            .select_from(Student)
            .where(Student.course_id == course.id, Student.status == "active")
        ).scalar_one()

        attendance_stats = db.execute(
            select(
                func.count().label("total_days"),
                func.sum(case((Attendance.status == "present", 1), else_=0)).label("present_days"),
            )
            .join(Student, Attendance.student_id == Student.id)
            .where(Student.course_id == course.id)
        ).first()

        average_attendance_percentage = None
        if attendance_stats and attendance_stats.total_days:
            average_attendance_percentage = round(
                (attendance_stats.present_days or 0) / attendance_stats.total_days * 100,
                2,
            )

        fees_assigned = db.execute(
            select(func.coalesce(func.sum(StudentFee.total_amount), 0))
            .join(Student, StudentFee.student_id == Student.id)
            .where(Student.course_id == course.id)
        ).scalar_one()

        payment_totals = (
            select(
                StudentFee.id,
                func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
            )
            .outerjoin(Payment, StudentFee.id == Payment.student_fee_id)
            .join(Student, StudentFee.student_id == Student.id)
            .where(Student.course_id == course.id)
            .group_by(StudentFee.id)
            .subquery()
        )

        fees_collected = db.execute(
            select(func.coalesce(func.sum(payment_totals.c.paid_amount), 0))
            .select_from(payment_totals)
        ).scalar_one()

        total_fees_pending = float(fees_assigned) - float(fees_collected)

        items.append(
            CourseReportItem(
                course_id=course.id,
                course_code=course.code,
                course_name=course.name,
                is_active=course.is_active,
                student_count=student_count,
                active_student_count=active_student_count,
                average_attendance_percentage=average_attendance_percentage,
                total_fees_assigned=fees_assigned,
                total_fees_collected=fees_collected,
                total_fees_pending=total_fees_pending,
            )
        )
    return items, total_items
