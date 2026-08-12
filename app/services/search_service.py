from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.course import Course
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User
from app.schemas.search import SearchResponse, SearchResult


def _pattern(query: str) -> str:
    return f"%{query.strip().lower()}%"


def _student_results(db: Session, pattern: str, limit: int) -> list[SearchResult]:
    full_name = func.lower(Student.first_name + " " + Student.last_name)
    statement = (
        select(Student, Course)
        .outerjoin(Course, Student.course_id == Course.id)
        .where(
            or_(
                func.lower(Student.student_code).like(pattern),
                func.lower(Student.first_name).like(pattern),
                func.lower(Student.last_name).like(pattern),
                func.lower(Student.email).like(pattern),
                full_name.like(pattern),
            )
        )
        .order_by(Student.first_name.asc(), Student.last_name.asc(), Student.id.asc())
        .limit(limit)
    )
    return [
        SearchResult(
            id=student.id,
            title=f"{student.first_name} {student.last_name}",
            subtitle=" - ".join(
                item
                for item in (student.student_code, course.name if course else None)
                if item
            ),
            type="student",
            url=f"/admin/students?search={student.student_code}",
        )
        for student, course in db.execute(statement).all()
    ]


def _course_results(db: Session, pattern: str, limit: int) -> list[SearchResult]:
    statement = (
        select(Course)
        .where(
            or_(
                func.lower(Course.name).like(pattern),
                func.lower(Course.code).like(pattern),
            )
        )
        .order_by(Course.name.asc(), Course.id.asc())
        .limit(limit)
    )
    return [
        SearchResult(
            id=course.id,
            title=course.name,
            subtitle=course.code,
            type="course",
            url=f"/admin/classes?search={course.code}",
        )
        for course in db.execute(statement).scalars().all()
    ]


def _subject_results(db: Session, pattern: str, limit: int) -> list[SearchResult]:
    statement = (
        select(Subject, Course)
        .join(Course, Subject.course_id == Course.id)
        .where(
            or_(
                func.lower(Subject.name).like(pattern),
                func.lower(Subject.code).like(pattern),
                func.lower(Course.name).like(pattern),
                func.lower(Course.code).like(pattern),
            )
        )
        .order_by(Subject.name.asc(), Subject.id.asc())
        .limit(limit)
    )
    return [
        SearchResult(
            id=subject.id,
            title=subject.name,
            subtitle=f"{subject.code} - {course.name}",
            type="subject",
            url="/admin/classes",
        )
        for subject, course in db.execute(statement).all()
    ]


def _batch_results(db: Session, pattern: str, limit: int) -> list[SearchResult]:
    statement = (
        select(Batch, Course)
        .join(Course, Batch.course_id == Course.id)
        .where(
            or_(
                func.lower(Batch.name).like(pattern),
                func.lower(Batch.section).like(pattern),
                func.lower(Course.name).like(pattern),
                func.lower(Course.code).like(pattern),
            )
        )
        .order_by(Batch.name.asc(), Batch.id.asc())
        .limit(limit)
    )
    return [
        SearchResult(
            id=batch.id,
            title=batch.name,
            subtitle=" - ".join(
                item for item in (course.name, batch.section) if item
            ),
            type="batch",
            url="/admin/classes",
        )
        for batch, course in db.execute(statement).all()
    ]


def _user_results(db: Session, pattern: str, limit: int) -> list[SearchResult]:
    statement = (
        select(User)
        .where(
            or_(
                func.lower(User.name).like(pattern),
                func.lower(User.email).like(pattern),
                func.lower(User.role).like(pattern),
            )
        )
        .order_by(User.name.asc(), User.id.asc())
        .limit(limit)
    )
    return [
        SearchResult(
            id=user.id,
            title=user.name,
            subtitle=f"{user.email} - {user.role}",
            type="user",
            url="/admin/settings",
        )
        for user in db.execute(statement).scalars().all()
    ]


def global_search(
    db: Session,
    *,
    query: str,
    include_users: bool = False,
    limit: int = 5,
) -> SearchResponse:
    pattern = _pattern(query)
    return SearchResponse(
        students=_student_results(db, pattern, limit),
        courses=_course_results(db, pattern, limit),
        subjects=_subject_results(db, pattern, limit),
        batches=_batch_results(db, pattern, limit),
        users=_user_results(db, pattern, limit) if include_users else [],
    )
