from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.schemas.batch import BatchCreate, BatchUpdate


def get_batch(db: Session, batch_id: int) -> Batch | None:
    return db.get(Batch, batch_id)


def get_batches(db: Session, skip: int = 0, limit: int = 100) -> list[Batch]:
    statement = select(Batch).offset(skip).limit(limit).order_by(Batch.name)
    return list(db.execute(statement).scalars().all())


def create_batch(db: Session, batch: BatchCreate) -> Batch:
    db_batch = Batch(**batch.model_dump())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch


def update_batch(db: Session, batch_id: int, batch: BatchUpdate) -> Batch | None:
    db_batch = db.get(Batch, batch_id)
    if not db_batch:
        return None

    update_data = batch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_batch, key, value)

    db.commit()
    db.refresh(db_batch)
    return db_batch


def get_batch_by_name(db: Session, name: str) -> Batch | None:
    statement = select(Batch).where(Batch.name == name.strip())
    return db.execute(statement).scalar_one_or_none()


def get_batches_paginated(
    db: Session,
    course_id: int | None = None,
    academic_year_id: int | None = None,
    semester_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Batch], int]:
    statement = select(Batch)
    if course_id is not None:
        statement = statement.where(Batch.course_id == course_id)
    if academic_year_id is not None:
        statement = statement.where(Batch.academic_year_id == academic_year_id)
    if semester_id is not None:
        statement = statement.where(Batch.semester_id == semester_id)

    total_statement = select(Batch)
    if course_id is not None:
        total_statement = total_statement.where(Batch.course_id == course_id)
    if academic_year_id is not None:
        total_statement = total_statement.where(Batch.academic_year_id == academic_year_id)
    if semester_id is not None:
        total_statement = total_statement.where(Batch.semester_id == semester_id)

    total = db.execute(total_statement).unique().scalars().all()
    items = db.execute(statement.offset(skip).limit(limit)).scalars().all()
    return items, len(total)


def batch_has_students(db: Session, batch_id: int) -> bool:
    from app.models.student import Student
    statement = select(Student).where(Student.batch_id == batch_id).limit(1)
    return db.execute(statement).scalar_one_or_none() is not None


def delete_batch(db: Session, batch_id: int) -> bool:
    db_batch = db.get(Batch, batch_id)
    if not db_batch:
        return False

    db.delete(db_batch)
    db.commit()
    return True
