from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.academic_year import AcademicYear
from app.schemas.academic_year import AcademicYearCreate, AcademicYearResponse, AcademicYearUpdate
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.services import academic_year_service


router = APIRouter(
    prefix="/academic-years",
    tags=["Academic Years"],
)


def _duplicate_detail(_error: IntegrityError) -> str:
    return "An academic year with this name already exists"


@router.post(
    "",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_academic_year(
    year_data: AcademicYearCreate,
    db: Session = Depends(get_db),
) -> AcademicYear:
    if academic_year_service.get_academic_year_by_name(db, year_data.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An academic year with this name already exists",
        )

    try:
        return academic_year_service.create_academic_year(db, year_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.get(
    "",
    response_model=PaginatedResponse[AcademicYearResponse],
    dependencies=[Depends(get_current_user)],
)
def get_academic_years(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    years, total_items = academic_year_service.get_academic_years_paginated(
        db,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return build_paginated_response(years, page, page_size, total_items)


@router.get(
    "/{year_id}",
    response_model=AcademicYearResponse,
    dependencies=[Depends(get_current_user)],
)
def get_academic_year(
    year_id: int,
    db: Session = Depends(get_db),
) -> AcademicYear:
    year = academic_year_service.get_academic_year(db, year_id)
    if year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found",
        )
    return year


@router.put(
    "/{year_id}",
    response_model=AcademicYearResponse,
    dependencies=[Depends(require_admin)],
)
def update_academic_year(
    year_id: int,
    year_data: AcademicYearUpdate,
    db: Session = Depends(get_db),
) -> AcademicYear:
    year = academic_year_service.get_academic_year(db, year_id)
    if year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found",
        )

    update_data = year_data.model_dump(exclude_unset=True)
    name = update_data.get("name")
    if name is not None and name != year.name:
        existing_year = academic_year_service.get_academic_year_by_name(db, name)
        if existing_year is not None and existing_year.id != year.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An academic year with this name already exists",
            )

    try:
        return academic_year_service.update_academic_year(db, year, year_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.delete(
    "/{year_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_academic_year(
    year_id: int,
    db: Session = Depends(get_db),
) -> Response:
    year = academic_year_service.get_academic_year(db, year_id)
    if year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found",
        )

    if academic_year_service.year_has_semesters(db, year_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete academic year because semesters are assigned to it",
        )

    academic_year_service.delete_academic_year(db, year)
    return Response(status_code=status.HTTP_204_NO_CONTENT)