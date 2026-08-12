from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.student import Student
from app.schemas.pagination import get_offset
from app.schemas.attendance import (
    AttendanceBulkItem,
    AttendanceCreate,
    AttendanceUpdate,
)


def get_attendance_by_id(db: Session, attendance_id: int) -> Attendance | None:
    statement = select(Attendance).where(Attendance.id == attendance_id)
    return db.execute(statement).scalar_one_or_none()


def get_attendance_for_student_date(
    db: Session,
    student_id: int,
    attendance_date: date,
) -> Attendance | None:
    statement = select(Attendance).where(
        Attendance.student_id == student_id,
        Attendance.date == attendance_date,
    )
    return db.execute(statement).scalar_one_or_none()


def get_existing_student_ids(db: Session, student_ids: set[int]) -> set[int]:
    if not student_ids:
        return set()

    statement = select(Student.id).where(Student.id.in_(student_ids))
    return set(db.execute(statement).scalars().all())


def get_attendance_records(
    db: Session,
    attendance_date: date | None = None,
    student_id: int | None = None,
    course_id: int | None = None,
    status: str | None = None,
) -> list[Attendance]:
    statement = select(Attendance)

    if course_id is not None:
        statement = statement.join(Student, Attendance.student_id == Student.id).where(
            Student.course_id == course_id,
        )

    if attendance_date is not None:
        statement = statement.where(Attendance.date == attendance_date)

    if student_id is not None:
        statement = statement.where(Attendance.student_id == student_id)

    if status is not None:
        statement = statement.where(Attendance.status == status)

    statement = statement.order_by(Attendance.date.desc(), Attendance.id.desc())
    return list(db.execute(statement).scalars().all())


def get_attendance_records_paginated(
    db: Session,
    attendance_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    student_id: int | None = None,
    course_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[Attendance], int]:
    statement = select(Attendance)

    if course_id is not None:
        statement = statement.join(Student, Attendance.student_id == Student.id).where(
            Student.course_id == course_id,
        )

    if attendance_date is not None:
        statement = statement.where(Attendance.date == attendance_date)
    else:
        if start_date is not None:
            statement = statement.where(Attendance.date >= start_date)

        if end_date is not None:
            statement = statement.where(Attendance.date <= end_date)

    if student_id is not None:
        statement = statement.where(Attendance.student_id == student_id)

    if status is not None:
        statement = statement.where(Attendance.status == status)

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    statement = (
        statement.order_by(
            Attendance.date.desc(),
            Attendance.updated_at.desc(),
            Attendance.id.desc(),
        )
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )

    return list(db.execute(statement).scalars().all()), total_items


def get_student_attendance(
    db: Session,
    student_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Attendance]:
    statement = select(Attendance).where(Attendance.student_id == student_id)

    if start_date is not None:
        statement = statement.where(Attendance.date >= start_date)

    if end_date is not None:
        statement = statement.where(Attendance.date <= end_date)

    statement = statement.order_by(Attendance.date.desc(), Attendance.id.desc())
    return list(db.execute(statement).scalars().all())


def get_attendance_by_date(db: Session, attendance_date: date) -> list[Attendance]:
    return get_attendance_records(db, attendance_date=attendance_date)


def get_students_for_course(db: Session, course_id: int) -> list[Student]:
    statement = select(Student).where(Student.course_id == course_id).order_by(
        Student.student_code,
        Student.id,
    )
    return list(db.execute(statement).scalars().all())


def get_course_attendance_by_date(
    db: Session,
    course_id: int,
    attendance_date: date,
) -> list[tuple[Student, Attendance | None]]:
    students = get_students_for_course(db, course_id)
    student_ids = [student.id for student in students]

    if not student_ids:
        return []

    statement = select(Attendance).where(
        Attendance.date == attendance_date,
        Attendance.student_id.in_(student_ids),
    )
    attendance_by_student_id = {
        attendance.student_id: attendance
        for attendance in db.execute(statement).scalars().all()
    }

    return [
        (student, attendance_by_student_id.get(student.id))
        for student in students
    ]


def create_attendance(
    db: Session,
    attendance_data: AttendanceCreate,
    marked_by: int,
) -> Attendance:
    attendance = Attendance(
        student_id=attendance_data.student_id,
        date=attendance_data.date,
        status=attendance_data.status.value,
        remarks=attendance_data.remarks,
        marked_by=marked_by,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def bulk_upsert_attendance(
    db: Session,
    attendance_date: date,
    records: list[AttendanceBulkItem],
    marked_by: int,
) -> tuple[int, int, list[Attendance]]:
    student_ids = [record.student_id for record in records]
    statement = select(Attendance).where(
        Attendance.date == attendance_date,
        Attendance.student_id.in_(student_ids),
    )
    existing_by_student_id = {
        attendance.student_id: attendance
        for attendance in db.execute(statement).scalars().all()
    }

    created = 0
    updated = 0
    result_by_student_id: dict[int, Attendance] = {}
    now = datetime.now(UTC)

    for record in records:
        attendance = existing_by_student_id.get(record.student_id)
        if attendance is None:
            attendance = Attendance(
                student_id=record.student_id,
                date=attendance_date,
                status=record.status.value,
                remarks=record.remarks,
                marked_by=marked_by,
            )
            db.add(attendance)
            created += 1
        else:
            attendance.status = record.status.value
            attendance.remarks = record.remarks
            attendance.marked_by = marked_by
            attendance.updated_at = now
            updated += 1

        result_by_student_id[record.student_id] = attendance

    db.commit()

    ordered_results = [result_by_student_id[record.student_id] for record in records]
    for attendance in ordered_results:
        db.refresh(attendance)

    return created, updated, ordered_results


def update_attendance(
    db: Session,
    attendance: Attendance,
    attendance_data: AttendanceUpdate,
    marked_by: int,
) -> Attendance:
    update_data = attendance_data.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        attendance.status = update_data["status"].value

    if "remarks" in update_data:
        attendance.remarks = update_data["remarks"]

    attendance.marked_by = marked_by
    attendance.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(attendance)
    return attendance


def delete_attendance(db: Session, attendance: Attendance) -> None:
    db.delete(attendance)
    db.commit()


def calculate_student_attendance_summary(
    db: Session,
    student_id: int,
) -> dict[str, int | float]:
    records = get_student_attendance(db, student_id)
    total_marked_days = len(records)
    present_days = sum(1 for record in records if record.status == "present")
    absent_days = sum(1 for record in records if record.status == "absent")
    late_days = sum(1 for record in records if record.status == "late")
    excused_days = sum(1 for record in records if record.status == "excused")
    attendance_percentage = (
        round((present_days / total_marked_days) * 100, 2)
        if total_marked_days
        else 0.0
    )

    return {
        "student_id": student_id,
        "total_marked_days": total_marked_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "late_days": late_days,
        "excused_days": excused_days,
        "attendance_percentage": attendance_percentage,
        "total_sessions": total_marked_days,
        "present": present_days,
        "absent": absent_days,
        "late": late_days,
        "excused": excused_days,
    }
