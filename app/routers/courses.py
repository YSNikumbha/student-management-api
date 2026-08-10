from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from app.services import course_service


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


def _duplicate_detail(_error: IntegrityError) -> str:
    return "A course with this code already exists"


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
) -> Course:
    if course_service.get_course_by_code(db, course_data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this code already exists",
        )

    try:
        return course_service.create_course(db, course_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.get(
    "",
    response_model=list[CourseResponse],
    dependencies=[Depends(get_current_user)],
)
def get_courses(db: Session = Depends(get_db)) -> list[Course]:
    return course_service.get_courses(db)


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(get_current_user)],
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
) -> Course:
    course = course_service.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return course


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)],
)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
) -> Course:
    course = course_service.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    update_data = course_data.model_dump(exclude_unset=True)
    code = update_data.get("code")
    if code is not None and code != course.code:
        existing_course = course_service.get_course_by_code(db, code)
        if existing_course is not None and existing_course.id != course.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A course with this code already exists",
            )

    try:
        return course_service.update_course(db, course, course_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
) -> Response:
    course = course_service.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if course_service.course_has_students(db, course_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete course because students are assigned to it",
        )

    course_service.delete_course(db, course)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
