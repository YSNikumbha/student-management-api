from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.classroom import ClassCreate, ClassResponse, ClassUpdate
from app.services import classroom_service

router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)


@router.get("", response_model=list[ClassResponse])
def get_classes(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("classes.view")),
) -> list[ClassResponse]:
    return [
        classroom_service.build_class_response(db, batch)
        for batch in classroom_service.get_classes(db)
    ]


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("classes.create")),
) -> ClassResponse:
    try:
        batch = classroom_service.create_class(db, class_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A class with this name already exists",
        ) from error
    batch = classroom_service.get_class(db, batch.id) or batch
    return classroom_service.build_class_response(db, batch)


@router.get("/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("classes.view")),
) -> ClassResponse:
    batch = classroom_service.get_class(db, class_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return classroom_service.build_class_response(db, batch)


@router.put("/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    class_data: ClassUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("classes.edit")),
) -> ClassResponse:
    batch = classroom_service.get_class(db, class_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    try:
        updated = classroom_service.update_class(db, class_id, class_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A class with this name already exists",
        ) from error
    updated = classroom_service.get_class(db, class_id) or updated
    return classroom_service.build_class_response(db, updated)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("classes.delete")),
) -> Response:
    batch = classroom_service.get_class(db, class_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    if classroom_service.class_has_students(db, class_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete class because students are assigned to it",
        )
    classroom_service.delete_class(db, class_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
