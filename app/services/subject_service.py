from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


def get_subject(db: Session, subject_id: int) -> Subject | None:
    return db.get(Subject, subject_id)


def get_subjects(db: Session, skip: int = 0, limit: int = 100) -> list[Subject]:
    statement = select(Subject).offset(skip).limit(limit).order_by(Subject.code)
    return list(db.execute(statement).scalars().all())


def create_subject(db: Session, subject: SubjectCreate) -> Subject:
    db_subject = Subject(**subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def update_subject(db: Session, subject_id: int, subject: SubjectUpdate) -> Subject | None:
    db_subject = db.get(Subject, subject_id)
    if not db_subject:
        return None

    update_data = subject.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_subject, key, value)

    db.commit()
    db.refresh(db_subject)
    return db_subject


def get_subject_by_code(db: Session, code: str) -> Subject | None:
    statement = select(Subject).where(Subject.code == code.strip().upper())
    return db.execute(statement).scalar_one_or_none()


def get_subjects_paginated(
    db: Session,
    course_id: int | None = None,
    semester_id: int | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Subject], int]:
    statement = select(Subject)
    if course_id is not None:
        statement = statement.where(Subject.course_id == course_id)
    if semester_id is not None:
        statement = statement.where(Subject.semester_id == semester_id)
    if search:
        statement = statement.where(Subject.code.ilike(f"%{search}%"))

    total_statement = select(Subject)
    if course_id is not None:
        total_statement = total_statement.where(Subject.course_id == course_id)
    if semester_id is not None:
        total_statement = total_statement.where(Subject.semester_id == semester_id)
    if search:
        total_statement = total_statement.where(Subject.code.ilike(f"%{search}%"))

    total = db.execute(total_statement).unique().scalars().all()
    items = db.execute(statement.offset(skip).limit(limit)).scalars().all()
    return items, len(total)


def delete_subject(db: Session, subject_id: int) -> bool:
    db_subject = db.get(Subject, subject_id)
    if not db_subject:
        return False

    db.delete(db_subject)
    db.commit()
    return True
