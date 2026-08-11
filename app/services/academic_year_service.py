from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.schemas.academic_year import AcademicYearCreate, AcademicYearUpdate


def get_academic_year(db: Session, year_id: int) -> AcademicYear | None:
    return db.get(AcademicYear, year_id)


def get_academic_years(db: Session, skip: int = 0, limit: int = 100) -> list[AcademicYear]:
    statement = select(AcademicYear).offset(skip).limit(limit).order_by(AcademicYear.start_date.desc())
    return list(db.execute(statement).scalars().all())


def create_academic_year(db: Session, year: AcademicYearCreate) -> AcademicYear:
    db_year = AcademicYear(**year.model_dump())
    db.add(db_year)
    db.commit()
    db.refresh(db_year)
    return db_year


def update_academic_year(db: Session, year_id: int, year: AcademicYearUpdate) -> AcademicYear | None:
    db_year = db.get(AcademicYear, year_id)
    if not db_year:
        return None

    update_data = year.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_year, key, value)

    db.commit()
    db.refresh(db_year)
    return db_year


def get_academic_year_by_name(db: Session, name: str) -> AcademicYear | None:
    statement = select(AcademicYear).where(AcademicYear.name == name.strip())
    return db.execute(statement).scalar_one_or_none()


def get_academic_years_paginated(
    db: Session,
    search: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[AcademicYear], int]:
    statement = select(AcademicYear)

    if search:
        statement = statement.where(AcademicYear.name.ilike(f"%{search}%"))
    if is_active is not None:
        statement = statement.where(AcademicYear.is_active == is_active)

    total_statement = select(AcademicYear)
    if search:
        total_statement = total_statement.where(AcademicYear.name.ilike(f"%{search}%"))
    if is_active is not None:
        total_statement = total_statement.where(AcademicYear.is_active == is_active)

    total = db.execute(total_statement).unique().scalars().all()
    items = db.execute(statement.offset(skip).limit(limit)).scalars().all()
    return items, len(total)


def year_has_semesters(db: Session, year_id: int) -> bool:
    from app.models.semester import Semester
    statement = select(Semester).where(Semester.academic_year_id == year_id).limit(1)
    return db.execute(statement).scalar_one_or_none() is not None


def delete_academic_year(db: Session, year_id: int) -> bool:
    db_year = db.get(AcademicYear, year_id)
    if not db_year:
        return False

    db.delete(db_year)
    db.commit()
    return True
