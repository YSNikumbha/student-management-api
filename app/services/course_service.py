from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.student import Student
from app.schemas.course import CourseCreate, CourseUpdate


def get_course_by_id(db: Session, course_id: int) -> Course | None:
    statement = select(Course).where(Course.id == course_id)
    return db.execute(statement).scalar_one_or_none()


def get_course_by_code(db: Session, code: str) -> Course | None:
    statement = select(Course).where(Course.code == code)
    return db.execute(statement).scalar_one_or_none()


def get_courses(db: Session) -> list[Course]:
    statement = select(Course).order_by(Course.id)
    return list(db.execute(statement).scalars().all())


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
