from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from statistics import mean
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession
from app.models.batch import Batch
from app.models.course import Course
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.subject import Subject
from app.schemas.attendance_session import AttendanceBulkCreate
from app.services import (
    academic_performance_service,
    attendance_session_service,
    classroom_service,
    fee_service,
)


def _money(value: Decimal | int | float | str | None) -> float:
    return float(fee_service.normalize_money(value))


def _student_name(student: Student) -> str:
    return f"{student.first_name} {student.last_name}".strip()


def _fee_status_for_student(db: Session, student: Student) -> str:
    fees = fee_service.get_student_fees(db, student.id)
    if not fees:
        return "paid"
    statuses = [fee_service.calculate_fee_status(fee, fee_service.calculate_paid_amount(db, fee.id)).value for fee in fees]
    if "overdue" in statuses:
        return "overdue"
    if "partial" in statuses:
        return "partial"
    if "unpaid" in statuses:
        return "pending"
    return "paid"


def get_students_ui(db: Session) -> dict[str, Any]:
    students = list(
        db.execute(
            select(Student)
            .options(selectinload(Student.batch).selectinload(Batch.course))
            .order_by(Student.created_at.desc(), Student.id.desc())
        ).scalars().all()
    )
    gpa_map = academic_performance_service.get_student_gpa_map(db, [student.id for student in students])
    rows = []
    for student in students:
        academic = gpa_map.get(student.id, {"gpa": 0.0, "percentage": 0.0, "grade": "F"})
        rows.append(
            {
                "id": student.id,
                "rollNo": student.student_code,
                "name": _student_name(student),
                "avatar": student.profile_photo,
                "email": student.email,
                "phone": student.phone,
                "classId": student.batch_id,
                "className": student.batch.name if student.batch else None,
                "section": student.batch.section if student.batch else None,
                "gender": student.gender,
                "dob": student.date_of_birth,
                "address": student.address,
                "parentName": student.parent_name,
                "parentPhone": student.parent_phone,
                "enrolledDate": student.admission_date or student.created_at.date(),
                "status": student.status,
                "bloodGroup": student.blood_group,
                "feeStatus": _fee_status_for_student(db, student),
                "gpa": academic["gpa"],
                "percentage": academic["percentage"],
                "grade": academic["grade"],
                "courseId": student.course_id,
            }
        )
    gpas = [float(row["gpa"]) for row in rows]
    return {
        "summary": {
            "total_students": len(rows),
            "active": sum(1 for row in rows if row["status"] == "active"),
            "fee_overdue": sum(1 for row in rows if row["feeStatus"] == "overdue"),
            "avg_gpa": round(mean(gpas), 2) if gpas else 0.0,
        },
        "items": rows,
    }


def get_classes_ui(db: Session) -> dict[str, Any]:
    classes = [
        classroom_service.build_class_response(db, batch).model_dump(mode="json")
        for batch in classroom_service.get_classes(db)
    ]
    return {
        "summary": {
            "total_classes": len(classes),
            "total_students": sum(item["student_count"] for item in classes),
            "grade_levels": len({item["grade"] for item in classes if item["grade"]}),
            "avg_class_size": round(
                sum(item["student_count"] for item in classes) / len(classes)
            ) if classes else 0,
        },
        "items": classes,
    }


def _monthly_attendance(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(select(Attendance).where(Attendance.date.is_not(None))).scalars().all()
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"present": 0, "absent": 0, "late": 0, "excused": 0})
    for record in rows:
        month = record.date.strftime("%b") if record.date else ""
        if record.status in grouped[month]:
            grouped[month][record.status] += 1
    return [
        {"month": month, **values}
        for month, values in grouped.items()
    ]


def _monthly_fees(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(select(Payment)).scalars().all()
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"collected": 0.0, "pending": 0.0})
    for payment in rows:
        month = payment.payment_date.strftime("%b")
        grouped[month]["collected"] += _money(payment.amount)

    unpaid_rows = fee_service.get_fees_paginated(db, page=1, page_size=1000)[0]
    for fee, paid in unpaid_rows:
        balance = fee_service.calculate_balance(fee.total_amount, paid)
        if balance > Decimal("0.00"):
            grouped[fee.due_date.strftime("%b")]["pending"] += _money(balance)
    return [{"month": month, **values} for month, values in grouped.items()]


def get_dashboard_ui(db: Session) -> dict[str, Any]:
    students_data = get_students_ui(db)
    classes_data = get_classes_ui(db)
    fee_summary = fee_service.get_fee_summary(db)
    attendance_monthly = _monthly_attendance(db)
    fee_monthly = _monthly_fees(db)
    academic = academic_performance_service.get_academic_report(db)

    total_attendance = sum(item["present"] + item["absent"] + item["late"] + item["excused"] for item in attendance_monthly)
    present_attendance = sum(item["present"] for item in attendance_monthly)
    attendance_rate = round((present_attendance / total_attendance) * 100, 2) if total_attendance else 0.0
    total_assigned = _money(fee_summary["total_assigned"])
    collected = _money(fee_summary["total_collected"])
    collection_rate = round((collected / total_assigned) * 100, 2) if total_assigned else 0.0

    return {
        "kpis": {
            "total_students": students_data["summary"]["total_students"],
            "attendance_rate": attendance_rate,
            "fee_collection": collected,
            "outstanding_dues": fee_summary["overdue_count"],
        },
        "attendance_overview": attendance_monthly,
        "fee_collection": fee_monthly,
        "recent_enrollments": students_data["items"][:6],
        "grade_distribution": academic["gpa_distribution"],
        "quick_stats": {
            "total_classes": classes_data["summary"]["total_classes"],
            "fee_collection_rate": collection_rate,
            "avg_attendance": attendance_rate,
            "active_students": students_data["summary"]["active"],
        },
    }


def get_attendance_ui(
    db: Session,
    *,
    selected_date: date,
    class_id: int | None = None,
) -> dict[str, Any]:
    classes_data = get_classes_ui(db)
    statement = (
        select(Attendance, Student, Batch)
        .join(Student, Attendance.student_id == Student.id)
        .outerjoin(Batch, Student.batch_id == Batch.id)
        .where(Attendance.date == selected_date)
    )
    if class_id is not None:
        statement = statement.where(Student.batch_id == class_id)
    rows = db.execute(statement).all()
    records = [
        {
            "id": attendance.id,
            "studentId": student.id,
            "studentName": _student_name(student),
            "rollNo": student.student_code,
            "date": attendance.date,
            "status": attendance.status,
            "classId": student.batch_id,
            "className": batch.name if batch else None,
            "note": attendance.remarks,
        }
        for attendance, student, batch in rows
    ]
    counts = {status: sum(1 for record in records if record["status"] == status) for status in ("present", "absent", "late", "excused")}
    return {
        "date": selected_date,
        "classes": classes_data["items"],
        "records": records,
        "summary": counts,
        "trends": _monthly_attendance(db),
    }


def mark_attendance_ui(
    db: Session,
    *,
    class_id: int,
    selected_date: date,
    records: list[dict[str, Any]],
    marked_by: int,
) -> dict[str, int]:
    batch = classroom_service.get_class(db, class_id)
    if batch is None:
        raise ValueError("Class not found")
    subject = db.execute(
        select(Subject)
        .where(
            Subject.course_id == batch.course_id,
            Subject.semester_id == batch.semester_id,
        )
        .order_by(Subject.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    if subject is None or batch.semester_id is None:
        raise ValueError("Class needs a semester and subject before attendance can be marked")
    start = datetime.combine(selected_date, time.min)
    end = datetime.combine(selected_date, time.max)
    session = db.execute(
        select(AttendanceSession).where(
            AttendanceSession.batch_id == class_id,
            AttendanceSession.subject_id == subject.id,
            AttendanceSession.date >= start,
            AttendanceSession.date <= end,
        )
    ).scalar_one_or_none()
    if session is None:
        session = AttendanceSession(
            date=datetime.combine(selected_date, time(hour=9)),
            course_id=batch.course_id,
            batch_id=batch.id,
            semester_id=batch.semester_id,
            subject_id=subject.id,
            session_name="Daily Attendance",
            created_by=marked_by,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    result = attendance_session_service.bulk_create_attendance(
        db,
        session.id,
        records,
        marked_by,
    )
    return result or {"created": 0, "updated": 0}


def get_fees_ui(db: Session) -> dict[str, Any]:
    fee_rows, _total = fee_service.get_fees_paginated(db, page=1, page_size=1000)
    records = []
    for fee, paid in fee_rows:
        response = fee_service.build_fee_response(db, fee, paid).model_dump(mode="json")
        payments = db.execute(
            select(Payment)
            .where(Payment.student_fee_id == fee.id)
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
        ).scalars().all()
        latest_payment = payments[0] if payments else None
        records.append(
            {
                **response,
                "invoice_number": response.get("invoice_number") or f"INV-{fee.due_date.year}-{fee.id:04d}",
                "fee_type": fee.title,
                "payment_method": latest_payment.payment_method if latest_payment else None,
                "paid_date": latest_payment.payment_date if latest_payment else None,
            }
        )
    summary = fee_service.get_fee_summary(db)
    total_billed = _money(summary["total_assigned"])
    collected = _money(summary["total_collected"])
    outstanding = _money(summary["total_pending"])
    return {
        "summary": {
            "total_billed": total_billed,
            "collected": collected,
            "outstanding": outstanding,
            "collection_rate": round((collected / total_billed) * 100, 2) if total_billed else 0.0,
        },
        "records": records,
        "fee_collection": _monthly_fees(db),
    }


def get_reports_ui(db: Session) -> dict[str, Any]:
    academic = academic_performance_service.get_academic_report(db)
    fees = get_fees_ui(db)
    attendance = _monthly_attendance(db)
    total_attendance = sum(item["present"] + item["absent"] + item["late"] + item["excused"] for item in attendance)
    present_attendance = sum(item["present"] for item in attendance)
    attendance_rate = round((present_attendance / total_attendance) * 100, 2) if total_attendance else 0.0
    return {
        "academic": academic,
        "attendance": {
            "summary": {
                "avg_attendance_rate": attendance_rate,
                "perfect_attendance": 0,
                "chronic_absentees": 0,
                "late_arrivals_avg": 0.0,
            },
            "monthly": attendance,
        },
        "finance": fees,
    }
