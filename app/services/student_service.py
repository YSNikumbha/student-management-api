from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.pagination import get_offset
from app.schemas.student import StudentCreate, StudentUpdate

STUDENT_SORT_COLUMNS = {
    "created_at": Student.created_at,
    "first_name": Student.first_name,
    "last_name": Student.last_name,
    "student_code": Student.student_code,
}


def get_student_by_id(db: Session, student_id: int) -> Student | None:
    statement = select(Student).where(Student.id == student_id)
    return db.execute(statement).scalar_one_or_none()


def get_student_by_email(db: Session, email: str) -> Student | None:
    statement = select(Student).where(Student.email == email)
    return db.execute(statement).scalar_one_or_none()


def get_student_by_code(db: Session, student_code: str) -> Student | None:
    statement = select(Student).where(Student.student_code == student_code)
    return db.execute(statement).scalar_one_or_none()


def get_students(db: Session) -> list[Student]:
    statement = select(Student).order_by(Student.id)
    return list(db.execute(statement).scalars().all())


def get_students_paginated(
    db: Session,
    search: str | None = None,
    course_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Student], int]:
    statement = select(Student)

    if search:
        search_pattern = f"%{search.lower()}%"
        statement = statement.where(
            or_(
                func.lower(Student.student_code).like(search_pattern),
                func.lower(Student.first_name).like(search_pattern),
                func.lower(Student.last_name).like(search_pattern),
                func.lower(Student.email).like(search_pattern),
                func.lower(Student.phone).like(search_pattern),
            ),
        )

    if course_id is not None:
        statement = statement.where(Student.course_id == course_id)

    if status is not None:
        statement = statement.where(Student.status == status)

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    sort_column = STUDENT_SORT_COLUMNS[sort_by]
    order_column = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    tie_breaker = Student.id.asc() if sort_order == "asc" else Student.id.desc()
    statement = (
        statement.order_by(order_column, tie_breaker)
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )

    return list(db.execute(statement).scalars().all()), total_items


def create_student(db: Session, student_data: StudentCreate) -> Student:
    student = Student(**student_data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(
    db: Session,
    student: Student,
    student_data: StudentUpdate,
) -> Student:
    update_data = student_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: Student) -> None:
    db.delete(student)
    db.commit()
