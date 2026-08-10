from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


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
