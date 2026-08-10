from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.services import course_service, fee_service, student_service


router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


def _duplicate_detail(error: IntegrityError) -> str:
    error_text = str(error.orig)
    if "students.email" in error_text:
        return "A student with this email already exists"
    if "students.student_code" in error_text:
        return "A student with this student code already exists"
    return "A student with this email or student code already exists"


def _validate_course_id(db: Session, course_id: int | None) -> None:
    if course_id is not None and course_service.get_course_by_id(db, course_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
) -> Student:
    _validate_course_id(db, student_data.course_id)

    if student_service.get_student_by_email(db, student_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email already exists",
        )

    if student_service.get_student_by_code(db, student_data.student_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this student code already exists",
        )

    try:
        return student_service.create_student(db, student_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.get(
    "",
    response_model=list[StudentResponse],
    dependencies=[Depends(get_current_user)],
)
def get_students(db: Session = Depends(get_db)) -> list[Student]:
    return student_service.get_students(db)


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(get_current_user)],
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
) -> Student:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(get_current_user)],
)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
) -> Student:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    update_data = student_data.model_dump(exclude_unset=True)
    if "course_id" in update_data:
        _validate_course_id(db, update_data["course_id"])

    email = update_data.get("email")
    if email is not None and email != student.email:
        existing_student = student_service.get_student_by_email(db, email)
        if existing_student is not None and existing_student.id != student.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this email already exists",
            )

    student_code = update_data.get("student_code")
    if student_code is not None and student_code != student.student_code:
        existing_student = student_service.get_student_by_code(db, student_code)
        if existing_student is not None and existing_student.id != student.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this student code already exists",
            )

    try:
        return student_service.update_student(db, student, student_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
) -> Response:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    if fee_service.student_has_fees(db, student.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete student because fee records exist",
        )

    try:
        student_service.delete_student(db, student)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete student because related records exist",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
