from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.subject import Subject
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services import subject_service


router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
)


def _duplicate_detail(_error: IntegrityError) -> str:
    return "A subject with this code already exists"


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_subject(
    subject_data: SubjectCreate,
    db: Session = Depends(get_db),
) -> Subject:
    if subject_service.get_subject_by_code(db, subject_data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A subject with this code already exists",
        )

    try:
        return subject_service.create_subject(db, subject_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.get(
    "",
    response_model=PaginatedResponse[SubjectResponse],
    dependencies=[Depends(get_current_user)],
)
def get_subjects(
    course_id: int | None = None,
    semester_id: int | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    skip = (page - 1) * page_size
    subjects, total_items = subject_service.get_subjects_paginated(
        db,
        course_id=course_id,
        semester_id=semester_id,
        search=search,
        skip=skip,
        limit=page_size,
    )
    return build_paginated_response(subjects, page, page_size, total_items)


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    dependencies=[Depends(get_current_user)],
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
) -> Subject:
    subject = subject_service.get_subject(db, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    return subject


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
    dependencies=[Depends(require_admin)],
)
def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    db: Session = Depends(get_db),
) -> Subject:
    subject = subject_service.get_subject(db, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    update_data = subject_data.model_dump(exclude_unset=True)
    code = update_data.get("code")
    if code is not None and code != subject.code:
        existing_subject = subject_service.get_subject_by_code(db, code)
        if existing_subject is not None and existing_subject.id != subject.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A subject with this code already exists",
            )

    try:
        return subject_service.update_subject(db, subject_id, subject_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
) -> Response:
    subject = subject_service.get_subject(db, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    subject_service.delete_subject(db, subject_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
