from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.semester import Semester
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.schemas.semester import SemesterCreate, SemesterResponse, SemesterUpdate
from app.services import semester_service


router = APIRouter(
    prefix="/semesters",
    tags=["Semesters"],
)


def _duplicate_detail(_error: IntegrityError) -> str:
    return "A semester with this number already exists for the selected academic year and course"


@router.post(
    "",
    response_model=SemesterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_semester(
    semester_data: SemesterCreate,
    db: Session = Depends(get_db),
) -> Semester:
    if semester_service.get_semester_by_unique_constraint(
        db, semester_data.academic_year_id, semester_data.course_id, semester_data.number
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A semester with this number already exists for the selected academic year and course",
        )

    try:
        return semester_service.create_semester(db, semester_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.get(
    "",
    response_model=PaginatedResponse[SemesterResponse],
    dependencies=[Depends(get_current_user)],
)
def get_semesters(
    academic_year_id: int | None = None,
    course_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    semesters, total_items = semester_service.get_semesters_paginated(
        db,
        academic_year_id=academic_year_id,
        course_id=course_id,
        page=page,
        page_size=page_size,
    )
    return build_paginated_response(semesters, page, page_size, total_items)


@router.get(
    "/{semester_id}",
    response_model=SemesterResponse,
    dependencies=[Depends(get_current_user)],
)
def get_semester(
    semester_id: int,
    db: Session = Depends(get_db),
) -> Semester:
    semester = semester_service.get_semester(db, semester_id)
    if semester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found",
        )
    return semester


@router.put(
    "/{semester_id}",
    response_model=SemesterResponse,
    dependencies=[Depends(require_admin)],
)
def update_semester(
    semester_id: int,
    semester_data: SemesterUpdate,
    db: Session = Depends(get_db),
) -> Semester:
    semester = semester_service.get_semester(db, semester_id)
    if semester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found",
        )

    update_data = semester_data.model_dump(exclude_unset=True)
    academic_year_id = update_data.get("academic_year_id", semester.academic_year_id)
    course_id = update_data.get("course_id", semester.course_id)
    number = update_data.get("number", semester.number)

    if (
        academic_year_id != semester.academic_year_id
        or course_id != semester.course_id
        or number != semester.number
    ):
        existing = semester_service.get_semester_by_unique_constraint(db, academic_year_id, course_id, number)
        if existing is not None and existing.id != semester.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A semester with this number already exists for the selected academic year and course",
            )

    try:
        return semester_service.update_semester(db, semester, semester_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.delete(
    "/{semester_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_semester(
    semester_id: int,
    db: Session = Depends(get_db),
) -> Response:
    semester = semester_service.get_semester(db, semester_id)
    if semester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semester not found",
        )

    if semester_service.semester_has_dependencies(db, semester_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete semester because it has associated subjects or batches",
        )

    semester_service.delete_semester(db, semester)
    return Response(status_code=status.HTTP_204_NO_CONTENT)