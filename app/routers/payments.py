from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.services import payment_service

router = APIRouter(
    prefix="/payments",
    tags=["Fees"],
)


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> Response:
    payment = payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    try:
        payment_service.delete_payment(db, payment)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment could not be deleted",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
