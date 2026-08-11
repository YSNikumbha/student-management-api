from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.semester import Semester
from app.schemas.semester import SemesterCreate, SemesterUpdate


def get_semester(db: Session, semester_id: int) -> Semester | None:
    return db.get(Semester, semester_id)


def get_semesters(db: Session, skip: int = 0, limit: int = 100) -> list[Semester]:
    statement = select(Semester).offset(skip).limit(limit).order_by(Semester.academic_year_id, Semester.number)
    return list(db.execute(statement).scalars().all())


def create_semester(db: Session, semester: SemesterCreate) -> Semester:
    db_semester = Semester(**semester.model_dump())
    db.add(db_semester)
    db.commit()
    db.refresh(db_semester)
    return db_semester


def update_semester(db: Session, semester_id: int, semester: SemesterUpdate) -> Semester | None:
    db_semester = db.get(Semester, semester_id)
    if not db_semester:
        return None

    update_data = semester.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_semester, key, value)

    db.commit()
    db.refresh(db_semester)
    return db_semester


def get_semester_by_unique_constraint(
    db: Session, academic_year_id: int, course_id: int, number: int
) -> Semester | None:
    statement = select(Semester).where(
        Semester.academic_year_id == academic_year_id,
        Semester.course_id == course_id,
        Semester.number == number,
    )
    return db.execute(statement).scalar_one_or_none()


def get_semesters_paginated(
    db: Session,
    academic_year_id: int | None = None,
    course_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Semester], int]:
    statement = select(Semester)
    if academic_year_id is not None:
        statement = statement.where(Semester.academic_year_id == academic_year_id)
    if course_id is not None:
        statement = statement.where(Semester.course_id == course_id)

    total_statement = select(Semester)
    if academic_year_id is not None:
        total_statement = total_statement.where(Semester.academic_year_id == academic_year_id)
    if course_id is not None:
        total_statement = total_statement.where(Semester.course_id == course_id)

    total = db.execute(total_statement).unique().scalars().all()
    items = db.execute(statement.offset(skip).limit(limit)).scalars().all()
    return items, len(total)


def semester_has_dependencies(db: Session, semester_id: int) -> bool:
    from app.models.batch import Batch
    from app.models.subject import Subject

    subject_statement = select(Subject).where(Subject.semester_id == semester_id).limit(1)
    batch_statement = select(Batch).where(Batch.semester_id == semester_id).limit(1)

    has_subjects = db.execute(subject_statement).scalar_one_or_none() is not None
    has_batches = db.execute(batch_statement).scalar_one_or_none() is not None
    return has_subjects or has_batches


def delete_semester(db: Session, semester_id: int) -> bool:
    db_semester = db.get(Semester, semester_id)
    if not db_semester:
        return False

    db.delete(db_semester)
    db.commit()
    return True
