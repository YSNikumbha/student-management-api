from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.schemas.student_fee import (
    FeeStatus,
    FeeSummaryResponse,
    StudentFeeCreate,
    StudentFeeDetailResponse,
    StudentFeeResponse,
    StudentFeeUpdate,
)
from app.services import fee_service, payment_service, student_service

router = APIRouter(
    prefix="/fees",
    tags=["Fees"],
)


def _get_fee_or_404(db: Session, fee_id: int):
    fee = fee_service.get_fee_by_id(db, fee_id)
    if fee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee record not found",
        )
    return fee


def _get_student_or_404(db: Session, student_id: int) -> None:
    if student_service.get_student_by_id(db, student_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )


@router.post(
    "",
    response_model=StudentFeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fee(
    fee_data: StudentFeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> StudentFeeResponse:
    _get_student_or_404(db, fee_data.student_id)

    try:
        fee = fee_service.create_fee(db, fee_data, created_by=current_user.id)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Fee record could not be created",
        ) from error

    return fee_service.build_fee_response(db, fee)


@router.get("/summary", response_model=FeeSummaryResponse)
def get_fee_summary(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FeeSummaryResponse:
    return FeeSummaryResponse(**fee_service.get_fee_summary(db))


@router.get("/student/{student_id}", response_model=list[StudentFeeResponse])
def get_student_fees(
    student_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[StudentFeeResponse]:
    _get_student_or_404(db, student_id)
    fees = fee_service.get_student_fees(db, student_id)
    return [fee_service.build_fee_response(db, fee) for fee in fees]


@router.get("", response_model=PaginatedResponse[StudentFeeResponse])
def get_fees(
    search: str | None = None,
    student_id: int | None = None,
    fee_status: FeeStatus | None = Query(default=None, alias="status"),
    course_id: int | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: Literal["due_date", "created_at", "total_amount"] = "due_date",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, list[StudentFeeResponse] | int]:
    if student_id is not None:
        _get_student_or_404(db, student_id)

    fee_rows, total_items = fee_service.get_fees_paginated(
        db,
        search=search,
        student_id=student_id,
        course_id=course_id,
        status=fee_status,
        due_before=due_before,
        due_after=due_after,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    responses = [
        fee_service.build_fee_response(db, fee, paid_amount)
        for fee, paid_amount in fee_rows
    ]

    return build_paginated_response(responses, page, page_size, total_items)


@router.get("/{fee_id}", response_model=StudentFeeDetailResponse)
def get_fee(
    fee_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> StudentFeeDetailResponse:
    fee = _get_fee_or_404(db, fee_id)
    fee_response = fee_service.build_fee_response(db, fee)
    payments = payment_service.get_payments_for_fee(db, fee.id)

    return StudentFeeDetailResponse(
        **fee_response.model_dump(),
        payments=payments,
    )


@router.put("/{fee_id}", response_model=StudentFeeResponse)
def update_fee(
    fee_id: int,
    fee_data: StudentFeeUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> StudentFeeResponse:
    fee = _get_fee_or_404(db, fee_id)
    update_data = fee_data.model_dump(exclude_unset=True)

    new_total = update_data.get("total_amount")
    if new_total is not None:
        paid_amount = fee_service.calculate_paid_amount(db, fee.id)
        if new_total < paid_amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Total fee amount cannot be less than amount already paid",
            )

    try:
        updated_fee = fee_service.update_fee(db, fee, fee_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Fee record could not be updated",
        ) from error

    return fee_service.build_fee_response(db, updated_fee)


@router.delete(
    "/{fee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_fee(
    fee_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> Response:
    fee = _get_fee_or_404(db, fee_id)

    if fee_service.fee_has_payments(db, fee.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete fee record because payments have already been recorded",
        )

    try:
        fee_service.delete_fee(db, fee)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Fee record could not be deleted",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{fee_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    fee_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentResponse:
    fee = _get_fee_or_404(db, fee_id)
    paid_amount = payment_service.calculate_total_paid(db, fee.id)
    balance = fee_service.calculate_balance(fee.total_amount, paid_amount)

    if payment_data.amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment amount must be greater than zero",
        )

    if payment_data.amount > balance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment amount cannot exceed remaining balance",
        )

    try:
        return payment_service.create_payment(
            db,
            fee.id,
            payment_data,
            recorded_by=current_user.id,
        )
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment could not be recorded",
        ) from error


@router.get("/{fee_id}/payments", response_model=list[PaymentResponse])
def get_fee_payments(
    fee_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[PaymentResponse]:
    fee = _get_fee_or_404(db, fee_id)
    return payment_service.get_payments_for_fee(db, fee.id)
