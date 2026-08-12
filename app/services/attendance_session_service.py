from datetime import UTC, datetime
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceStatus
from app.models.attendance_session import AttendanceSession
from app.schemas.attendance_session import (
    AttendanceSessionCreate,
    AttendanceSessionUpdate,
    AttendanceSessionWithDetails,
    AttendanceBulkCreate,
)


def get_attendance_session(db: Session, session_id: int) -> AttendanceSession | None:
    return db.get(AttendanceSession, session_id)


def get_attendance_sessions(
    db: Session,
    course_id: int | None = None,
    batch_id: int | None = None,
    semester_id: int | None = None,
    subject_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[AttendanceSession], int]:
    statement = select(AttendanceSession)
    if course_id is not None:
        statement = statement.where(AttendanceSession.course_id == course_id)
    if batch_id is not None:
        statement = statement.where(AttendanceSession.batch_id == batch_id)
    if semester_id is not None:
        statement = statement.where(AttendanceSession.semester_id == semester_id)
    if subject_id is not None:
        statement = statement.where(AttendanceSession.subject_id == subject_id)

    total_statement = select(func.count()).select_from(AttendanceSession)
    if course_id is not None:
        total_statement = total_statement.where(AttendanceSession.course_id == course_id)
    if batch_id is not None:
        total_statement = total_statement.where(AttendanceSession.batch_id == batch_id)
    if semester_id is not None:
        total_statement = total_statement.where(AttendanceSession.semester_id == semester_id)
    if subject_id is not None:
        total_statement = total_statement.where(AttendanceSession.subject_id == subject_id)

    total = db.execute(total_statement).scalar_one()
    items = db.execute(
        statement.order_by(AttendanceSession.date.desc(), AttendanceSession.id.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()
    return items, total


def create_attendance_session(db: Session, session: AttendanceSessionCreate, created_by: int) -> AttendanceSession:
    from app.models.course import Course
    from app.models.semester import Semester
    from app.models.batch import Batch
    from app.models.subject import Subject
    
    # Validate that all referenced resources exist and have consistent relationships
    course = db.get(Course, session.course_id)
    if not course:
        raise ValueError(f"Course with id {session.course_id} not found")
    
    semester = db.get(Semester, session.semester_id)
    if not semester:
        raise ValueError(f"Semester with id {session.semester_id} not found")
    
    batch = db.get(Batch, session.batch_id)
    if not batch:
        raise ValueError(f"Batch with id {session.batch_id} not found")
    
    subject = db.get(Subject, session.subject_id)
    if not subject:
        raise ValueError(f"Subject with id {session.subject_id} not found")
    
    # Validate cross-relationships
    if batch.course_id != session.course_id:
        raise ValueError(f"Batch {batch.id} does not belong to course {session.course_id}")
    
    if semester.course_id != session.course_id:
        raise ValueError(f"Semester {semester.id} does not belong to course {session.course_id}")
    
    if subject.course_id != session.course_id:
        raise ValueError(f"Subject {subject.id} does not belong to course {session.course_id}")
    
    if subject.semester_id != session.semester_id:
        raise ValueError(f"Subject {subject.id} does not belong to semester {session.semester_id}")
    
    if batch.academic_year_id != semester.academic_year_id:
        raise ValueError(f"Batch {batch.id} and semester {semester.id} belong to different academic years")
    
    db_session = AttendanceSession(**session.model_dump(), created_by=created_by)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_attendance_session(
    db: Session, session_id: int, session: AttendanceSessionUpdate
) -> AttendanceSession | None:
    db_session = db.get(AttendanceSession, session_id)
    if not db_session:
        return None

    update_data = session.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_session, key, value)

    db_session.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_attendance_session(db: Session, session_id: int) -> bool:
    db_session = db.get(AttendanceSession, session_id)
    if not db_session:
        return False

    db.delete(db_session)
    db.commit()
    return True


def get_session_students(db: Session, session_id: int) -> list[dict]:
    from app.models.student import Student

    session = db.get(AttendanceSession, session_id)
    if not session:
        return []

    statement = (
        select(Student, Attendance)
        .outerjoin(
            Attendance,
            (Attendance.student_id == Student.id)
            & (Attendance.attendance_session_id == session_id),
        )
        .where(
            Student.batch_id == session.batch_id,
            or_(Student.course_id == session.course_id, Student.course_id.is_(None)),
        )
        .order_by(Student.student_code, Student.id)
    )

    results = db.execute(statement).all()
    students = []
    for student, attendance in results:
        students.append({
            "student_id": student.id,
            "student_code": student.student_code,
            "student_name": f"{student.first_name} {student.last_name}",
            "attendance_id": attendance.id if attendance else None,
            "status": attendance.status if attendance else None,
            "remarks": attendance.remarks if attendance else None,
        })

    return students


def bulk_create_attendance(
    db: Session,
    session_id: int,
    records: list[dict],
    marked_by: int,
) -> dict[str, int] | None:
    from app.models.student import Student
    
    session = db.get(AttendanceSession, session_id)
    if not session:
        return None

    if not records:
        return {"created": 0, "updated": 0}

    record_by_student_id = {record["student_id"]: record for record in records}
    student_ids = set(record_by_student_id)
    students = db.execute(
        select(Student).where(
            Student.id.in_(student_ids),
            Student.batch_id == session.batch_id,
            or_(Student.course_id == session.course_id, Student.course_id.is_(None)),
        )
    ).scalars().all()

    valid_student_ids = {student.id for student in students}
    invalid_student_ids = sorted(student_ids - valid_student_ids)
    if invalid_student_ids:
        raise ValueError(
            "Students are not assigned to this session batch/course: "
            + ", ".join(str(student_id) for student_id in invalid_student_ids)
        )

    existing_records = db.execute(
        select(Attendance).where(
            Attendance.attendance_session_id == session_id,
            Attendance.student_id.in_(student_ids),
        )
    ).scalars().all()
    existing_by_student_id = {
        attendance.student_id: attendance for attendance in existing_records
    }

    created = 0
    updated = 0
    session_date = session.date.date() if session.date else None
    now = datetime.now(UTC)

    try:
        for student_id, record in record_by_student_id.items():
            attendance = existing_by_student_id.get(student_id)
            if attendance is None:
                attendance = Attendance(
                    attendance_session_id=session_id,
                    student_id=student_id,
                    date=session_date,
                    status=record["status"],
                    remarks=record.get("remarks"),
                    marked_by=marked_by,
                )
                db.add(attendance)
                created += 1
            else:
                attendance.status = record["status"]
                attendance.remarks = record.get("remarks")
                attendance.marked_by = marked_by
                if attendance.date is None:
                    attendance.date = session_date
                attendance.updated_at = now
                updated += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"created": created, "updated": updated}


def get_student_attendance_summary(db: Session, student_id: int) -> dict:
    from app.models.student import Student

    student = db.get(Student, student_id)
    if not student:
        return {}

    statement = (
        select(
            func.count(Attendance.id).label("total_sessions"),
            func.sum(case((Attendance.status == AttendanceStatus.present, 1), else_=0)).label("present"),
            func.sum(case((Attendance.status == AttendanceStatus.absent, 1), else_=0)).label("absent"),
            func.sum(case((Attendance.status == AttendanceStatus.late, 1), else_=0)).label("late"),
            func.sum(case((Attendance.status == AttendanceStatus.excused, 1), else_=0)).label("excused"),
        )
        .where(Attendance.student_id == student_id)
    )

    result = db.execute(statement).one()
    total = result.total_sessions or 0
    present = result.present or 0
    percentage = (present / total * 100) if total > 0 else 0.0

    return {
        "student_id": student_id,
        "student_name": f"{student.first_name} {student.last_name}",
        "total_sessions": total,
        "present": present,
        "absent": result.absent or 0,
        "late": result.late or 0,
        "excused": result.excused or 0,
        "attendance_percentage": round(percentage, 2),
    }


def get_student_subject_summary(db: Session, student_id: int) -> list[dict]:
    from app.models.student import Student
    from app.models.subject import Subject

    student = db.get(Student, student_id)
    if not student:
        return []

    statement = (
        select(
            Subject.id,
            Subject.code,
            Subject.name,
            func.count(Attendance.id).label("total_sessions"),
            func.sum(case((Attendance.status == AttendanceStatus.present, 1), else_=0)).label("present"),
        )
        .join(AttendanceSession, AttendanceSession.subject_id == Subject.id)
        .outerjoin(Attendance, (Attendance.attendance_session_id == AttendanceSession.id) & (Attendance.student_id == student_id))
        .where(AttendanceSession.batch_id == student.batch_id)
        .group_by(Subject.id, Subject.code, Subject.name)
    )

    results = db.execute(statement).all()
    summaries = []
    for subject_id, code, name, total, present in results:
        total = total or 0
        present = present or 0
        percentage = (present / total * 100) if total > 0 else 0.0
        summaries.append({
            "subject_id": subject_id,
            "subject_code": code,
            "subject_name": name,
            "total_sessions": total,
            "present": present,
            "attendance_percentage": round(percentage, 2),
        })

    return summaries
