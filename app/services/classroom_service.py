from __future__ import annotations

from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.batch import Batch
from app.models.student import Student
from app.schemas.batch import BatchCreate, BatchUpdate
from app.schemas.classroom import ClassCreate, ClassResponse, ClassUpdate
from app.services import academic_performance_service, batch_service


def get_class(db: Session, class_id: int) -> Batch | None:
    statement = (
        select(Batch)
        .options(
            selectinload(Batch.course),
            selectinload(Batch.semester),
            selectinload(Batch.class_teacher),
            selectinload(Batch.students),
        )
        .where(Batch.id == class_id)
    )
    return db.execute(statement).scalar_one_or_none()


def get_classes(db: Session) -> list[Batch]:
    statement = (
        select(Batch)
        .options(
            selectinload(Batch.course),
            selectinload(Batch.semester),
            selectinload(Batch.class_teacher),
            selectinload(Batch.students),
        )
        .order_by(Batch.name.asc(), Batch.id.asc())
    )
    return list(db.execute(statement).scalars().all())


def create_class(db: Session, data: ClassCreate) -> Batch:
    return batch_service.create_batch(db, BatchCreate(**data.model_dump()))


def update_class(db: Session, class_id: int, data: ClassUpdate) -> Batch | None:
    return batch_service.update_batch(db, class_id, BatchUpdate(**data.model_dump(exclude_unset=True)))


def delete_class(db: Session, class_id: int) -> bool:
    return batch_service.delete_batch(db, class_id)


def class_has_students(db: Session, class_id: int) -> bool:
    return batch_service.batch_has_students(db, class_id)


def build_class_response(db: Session, batch: Batch) -> ClassResponse:
    students = list(batch.students)
    gpa_map = academic_performance_service.get_student_gpa_map(db, [student.id for student in students])
    gpas = [float(summary["gpa"]) for summary in gpa_map.values()]
    semester_label = f"Semester {batch.semester.number}" if batch.semester else None
    return ClassResponse(
        id=batch.id,
        name=batch.name,
        program=batch.course.name if batch.course else None,
        grade=semester_label,
        section=batch.section,
        teacher=batch.class_teacher.name if batch.class_teacher else None,
        class_teacher_id=batch.class_teacher_id,
        student_count=len(students),
        average_gpa=round(mean(gpas), 2) if gpas else 0.0,
        room=batch.room,
        schedule=batch.schedule,
        course_id=batch.course_id,
        academic_year_id=batch.academic_year_id,
        semester_id=batch.semester_id,
        is_active=batch.is_active,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


def get_class_counts(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(Student.batch_id, func.count(Student.id)).group_by(Student.batch_id)
    ).all()
    return {batch_id: count for batch_id, count in rows if batch_id is not None}
