from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.batch import Batch
from app.schemas.batch import BatchCreate, BatchResponse, BatchUpdate
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.services import batch_service


router = APIRouter(
    prefix="/batches",
    tags=["Batches"],
)


def _duplicate_detail(_error: IntegrityError) -> str:
    return "A batch with this name already exists"


@router.post(
    "",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_batch(
    batch_data: BatchCreate,
    db: Session = Depends(get_db),
) -> Batch:
    if batch_service.get_batch_by_name(db, batch_data.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A batch with this name already exists",
        )

    try:
        return batch_service.create_batch(db, batch_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.get(
    "",
    response_model=PaginatedResponse[BatchResponse],
    dependencies=[Depends(get_current_user)],
)
def get_batches(
    course_id: int | None = None,
    academic_year_id: int | None = None,
    semester_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    skip = (page - 1) * page_size
    batches, total_items = batch_service.get_batches_paginated(
        db,
        course_id=course_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        skip=skip,
        limit=page_size,
    )
    return build_paginated_response(batches, page, page_size, total_items)


@router.get(
    "/{batch_id}",
    response_model=BatchResponse,
    dependencies=[Depends(get_current_user)],
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
) -> Batch:
    batch = batch_service.get_batch(db, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )
    return batch


@router.put(
    "/{batch_id}",
    response_model=BatchResponse,
    dependencies=[Depends(require_admin)],
)
def update_batch(
    batch_id: int,
    batch_data: BatchUpdate,
    db: Session = Depends(get_db),
) -> Batch:
    batch = batch_service.get_batch(db, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

    update_data = batch_data.model_dump(exclude_unset=True)
    name = update_data.get("name")
    if name is not None and name != batch.name:
        existing_batch = batch_service.get_batch_by_name(db, name)
        if existing_batch is not None and existing_batch.id != batch.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A batch with this name already exists",
            )

    try:
        return batch_service.update_batch(db, batch_id, batch_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error


@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
) -> Response:
    batch = batch_service.get_batch(db, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

    if batch_service.batch_has_students(db, batch_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete batch because students are assigned to it",
        )

    batch_service.delete_batch(db, batch_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
