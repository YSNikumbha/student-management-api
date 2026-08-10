from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.student import Student
from app.schemas.pagination import get_offset
from app.schemas.course import CourseCreate, CourseUpdate

COURSE_SORT_COLUMNS = {
    "name": Course.name,
    "code": Course.code,
    "created_at": Course.created_at,
}


def get_course_by_id(db: Session, course_id: int) -> Course | None:
    statement = select(Course).where(Course.id == course_id)
    return db.execute(statement).scalar_one_or_none()


def get_course_by_code(db: Session, code: str) -> Course | None:
    statement = select(Course).where(Course.code == code)
    return db.execute(statement).scalar_one_or_none()


def get_courses(db: Session) -> list[Course]:
    statement = select(Course).order_by(Course.id)
    return list(db.execute(statement).scalars().all())


def get_courses_paginated(
    db: Session,
    search: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Course], int]:
    statement = select(Course)

    if search:
        search_pattern = f"%{search.lower()}%"
        statement = statement.where(
            or_(
                func.lower(Course.code).like(search_pattern),
                func.lower(Course.name).like(search_pattern),
                func.lower(Course.description).like(search_pattern),
            ),
        )

    if is_active is not None:
        statement = statement.where(Course.is_active == is_active)

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    sort_column = COURSE_SORT_COLUMNS[sort_by]
    order_column = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    tie_breaker = Course.id.asc() if sort_order == "asc" else Course.id.desc()
    statement = (
        statement.order_by(order_column, tie_breaker)
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )

    return list(db.execute(statement).scalars().all()), total_items


def create_course(db: Session, course_data: CourseCreate) -> Course:
    course = Course(**course_data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(
    db: Session,
    course: Course,
    course_data: CourseUpdate,
) -> Course:
    update_data = course_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()


def course_has_students(db: Session, course_id: int) -> bool:
    statement = select(Student.id).where(Student.course_id == course_id).limit(1)
    return db.execute(statement).first() is not None
