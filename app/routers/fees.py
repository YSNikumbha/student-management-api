from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_fee_manager, require_payment_recorder
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.schemas.fee_structure import (
    FeeCategoryCreate,
    FeeCategoryResponse,
    FeeCategoryUpdate,
    FeeInstallmentCreate,
    FeeInstallmentResponse,
    FeeInstallmentUpdate,
    FeeStructureAssignRequest,
    FeeStructureAssignResponse,
    FeeStructureCreate,
    FeeStructureResponse,
    FeeStructureUpdate,
)
from app.schemas.student_fee import (
    FeeStatus,
    FeeSummaryResponse,
    StudentFeeCreate,
    StudentFeeDetailResponse,
    StudentFeeResponse,
    StudentFeeUpdate,
)
from app.services import audit_service, fee_service, payment_service, student_service

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


def _get_category_or_404(db: Session, category_id: int):
    category = fee_service.get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee category not found",
        )
    return category


def _get_structure_or_404(db: Session, structure_id: int):
    structure = fee_service.get_structure_by_id(db, structure_id)
    if structure is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee structure not found",
        )
    return structure


def _get_installment_or_404(db: Session, installment_id: int):
    installment = fee_service.get_installment_by_id(db, installment_id)
    if installment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee installment not found",
        )
    return installment


def _validate_structure_relationships(
    db: Session,
    *,
    course_id: int,
    academic_year_id: int,
    semester_id: int | None,
    category_id: int,
) -> None:
    if fee_service.get_course(db, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if fee_service.get_academic_year(db, academic_year_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    category = fee_service.get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee category not found")
    if semester_id is not None:
        semester = fee_service.get_semester(db, semester_id)
        if semester is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")
        if semester.course_id != course_id or semester.academic_year_id != academic_year_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Semester must belong to the selected course and academic year",
            )


@router.get("/categories", response_model=PaginatedResponse[FeeCategoryResponse])
def get_fee_categories(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict:
    categories, total_items = fee_service.get_categories_paginated(
        db,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return build_paginated_response(categories, page, page_size, total_items)


@router.post(
    "/categories",
    response_model=FeeCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fee_category(
    category_data: FeeCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
):
    if fee_service.get_category_by_name(db, category_data.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A fee category with this name already exists",
        )
    category = fee_service.create_category(db, category_data)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_category_created",
        entity_type="fee_category",
        entity_id=category.id,
        description=f"Fee category {category.name} created",
        ip_address=audit_service.get_request_ip(request),
    )
    return category


@router.put("/categories/{category_id}", response_model=FeeCategoryResponse)
def update_fee_category(
    category_id: int,
    category_data: FeeCategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
):
    category = _get_category_or_404(db, category_id)
    update_data = category_data.model_dump(exclude_unset=True)
    name = update_data.get("name")
    if name is not None:
        existing = fee_service.get_category_by_name(db, name)
        if existing is not None and existing.id != category.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A fee category with this name already exists",
            )
    updated_category = fee_service.update_category(db, category, category_data)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_category_updated",
        entity_type="fee_category",
        entity_id=updated_category.id,
        description=f"Fee category {updated_category.name} updated",
        metadata_json={"updated_fields": sorted(update_data.keys())},
        ip_address=audit_service.get_request_ip(request),
    )
    return updated_category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_category(
    category_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_fee_manager),
) -> Response:
    category = _get_category_or_404(db, category_id)
    if fee_service.category_has_structures(db, category.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete fee category because fee structures use it",
        )
    fee_service.delete_category(db, category)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/structures", response_model=PaginatedResponse[FeeStructureResponse])
def get_fee_structures(
    search: str | None = None,
    course_id: int | None = None,
    academic_year_id: int | None = None,
    semester_id: int | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict:
    structures, total_items = fee_service.get_structures_paginated(
        db,
        search=search,
        course_id=course_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        category_id=category_id,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    responses = [fee_service.build_structure_response(structure) for structure in structures]
    return build_paginated_response(responses, page, page_size, total_items)


@router.post(
    "/structures",
    response_model=FeeStructureResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fee_structure(
    structure_data: FeeStructureCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
) -> FeeStructureResponse:
    _validate_structure_relationships(
        db,
        course_id=structure_data.course_id,
        academic_year_id=structure_data.academic_year_id,
        semester_id=structure_data.semester_id,
        category_id=structure_data.category_id,
    )
    structure = fee_service.create_structure(db, structure_data)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_structure_created",
        entity_type="fee_structure",
        entity_id=structure.id,
        description=f"Fee structure {structure.name} created",
        metadata_json={"total_amount": structure.total_amount},
        ip_address=audit_service.get_request_ip(request),
    )
    return fee_service.build_structure_response(structure)


@router.get("/structures/{structure_id}", response_model=FeeStructureResponse)
def get_fee_structure(
    structure_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FeeStructureResponse:
    structure = _get_structure_or_404(db, structure_id)
    return fee_service.build_structure_response(structure)


@router.put("/structures/{structure_id}", response_model=FeeStructureResponse)
def update_fee_structure(
    structure_id: int,
    structure_data: FeeStructureUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
) -> FeeStructureResponse:
    structure = _get_structure_or_404(db, structure_id)
    update_data = structure_data.model_dump(exclude_unset=True)
    _validate_structure_relationships(
        db,
        course_id=update_data.get("course_id", structure.course_id),
        academic_year_id=update_data.get("academic_year_id", structure.academic_year_id),
        semester_id=update_data.get("semester_id", structure.semester_id),
        category_id=update_data.get("category_id", structure.category_id),
    )
    updated_structure = fee_service.update_structure(db, structure, structure_data)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_structure_updated",
        entity_type="fee_structure",
        entity_id=updated_structure.id,
        description=f"Fee structure {updated_structure.name} updated",
        metadata_json={"updated_fields": sorted(update_data.keys())},
        ip_address=audit_service.get_request_ip(request),
    )
    return fee_service.build_structure_response(updated_structure)


@router.delete("/structures/{structure_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_structure(
    structure_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_fee_manager),
) -> Response:
    structure = _get_structure_or_404(db, structure_id)
    if fee_service.structure_has_assignments(db, structure.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete fee structure because assignments exist",
        )
    fee_service.delete_structure(db, structure)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/structures/{structure_id}/assign",
    response_model=FeeStructureAssignResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_fee_structure(
    structure_id: int,
    assignment_data: FeeStructureAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
) -> FeeStructureAssignResponse:
    structure = _get_structure_or_404(db, structure_id)
    if not structure.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign an inactive fee structure",
        )
    if assignment_data.student_id is not None:
        student = student_service.get_student_by_id(db, assignment_data.student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        if student.course_id is not None and student.course_id != structure.course_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student must belong to the fee structure course",
            )
    else:
        batch = fee_service.get_batch(db, assignment_data.batch_id)
        if batch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
        if batch.course_id != structure.course_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch must belong to the fee structure course",
            )
    try:
        created, skipped, student_fee_ids = fee_service.assign_structure(
            db,
            structure,
            assignment_data,
            created_by=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_structure_assigned",
        entity_type="fee_structure",
        entity_id=structure.id,
        description=f"Fee structure {structure.name} assigned",
        metadata_json={
            "created": created,
            "skipped": skipped,
            "student_fee_ids": student_fee_ids,
        },
        ip_address=audit_service.get_request_ip(request),
    )
    return FeeStructureAssignResponse(
        created=created,
        skipped=skipped,
        student_fee_ids=student_fee_ids,
    )


@router.get("/{fee_id}/installments", response_model=list[FeeInstallmentResponse])
def get_fee_installments(
    fee_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[FeeInstallmentResponse]:
    fee = _get_fee_or_404(db, fee_id)
    installments = fee_service.get_installments_for_fee(db, fee.id)
    return [fee_service.build_installment_response(db, installment) for installment in installments]


@router.post(
    "/{fee_id}/installments",
    response_model=FeeInstallmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fee_installment(
    fee_id: int,
    installment_data: FeeInstallmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
) -> FeeInstallmentResponse:
    fee = _get_fee_or_404(db, fee_id)
    try:
        installment = fee_service.create_installment(db, fee, installment_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_installment_created",
        entity_type="fee_installment",
        entity_id=installment.id,
        description=f"Installment {installment.title} created",
        metadata_json={"student_fee_id": fee.id, "amount": installment.amount},
        ip_address=audit_service.get_request_ip(request),
    )
    return fee_service.build_installment_response(db, installment)


@router.put("/installments/{installment_id}", response_model=FeeInstallmentResponse)
def update_fee_installment(
    installment_id: int,
    installment_data: FeeInstallmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
) -> FeeInstallmentResponse:
    installment = _get_installment_or_404(db, installment_id)
    fee = _get_fee_or_404(db, installment.student_fee_id)
    try:
        updated_installment = fee_service.update_installment(
            db,
            fee,
            installment,
            installment_data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_installment_updated",
        entity_type="fee_installment",
        entity_id=updated_installment.id,
        description=f"Installment {updated_installment.title} updated",
        metadata_json={"updated_fields": sorted(installment_data.model_dump(exclude_unset=True).keys())},
        ip_address=audit_service.get_request_ip(request),
    )
    return fee_service.build_installment_response(db, updated_installment)


@router.delete("/installments/{installment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_installment(
    installment_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_fee_manager),
) -> Response:
    installment = _get_installment_or_404(db, installment_id)
    if fee_service.installment_has_payments(db, installment.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete installment because payments are allocated to it",
        )
    fee_service.delete_installment(db, installment)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "",
    response_model=StudentFeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fee(
    fee_data: StudentFeeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
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

    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_created",
        entity_type="student_fee",
        entity_id=fee.id,
        description=f"Fee {fee.title} created",
        metadata_json={
            "student_id": fee.student_id,
            "total_amount": fee.total_amount,
            "due_date": fee.due_date,
        },
        ip_address=audit_service.get_request_ip(request),
    )
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
    installments = fee_service.get_installments_for_fee(db, fee.id)

    return StudentFeeDetailResponse(
        **fee_response.model_dump(),
        payments=payments,
        installments=[
            fee_service.build_installment_response(db, installment)
            for installment in installments
        ],
    )


@router.put("/{fee_id}", response_model=StudentFeeResponse)
def update_fee(
    fee_id: int,
    fee_data: StudentFeeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
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

    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="fee_updated",
        entity_type="student_fee",
        entity_id=updated_fee.id,
        description=f"Fee {updated_fee.title} updated",
        metadata_json={"updated_fields": sorted(update_data.keys())},
        ip_address=audit_service.get_request_ip(request),
    )
    return fee_service.build_fee_response(db, updated_fee)


@router.delete(
    "/{fee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_fee(
    fee_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_fee_manager),
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_payment_recorder),
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

    if payment_data.fee_installment_id is not None:
        installment = fee_service.get_installment_by_id(db, payment_data.fee_installment_id)
        if installment is None or installment.student_fee_id != fee.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fee installment not found",
            )
        installment_paid = fee_service.calculate_installment_paid_amount(db, installment.id)
        installment_balance = fee_service.normalize_money(installment.amount) - installment_paid
        if payment_data.amount > installment_balance:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment amount cannot exceed installment balance",
            )

    try:
        payment = payment_service.create_payment(
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
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="payment_recorded",
        entity_type="payment",
        entity_id=payment.id,
        description="Payment recorded",
        metadata_json={
            "student_fee_id": fee.id,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "payment_date": payment.payment_date,
            "fee_installment_id": payment.fee_installment_id,
            "receipt_number": payment.receipt_number,
        },
        ip_address=audit_service.get_request_ip(request),
    )
    return payment


@router.get("/{fee_id}/payments", response_model=list[PaymentResponse])
def get_fee_payments(
    fee_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[PaymentResponse]:
    fee = _get_fee_or_404(db, fee_id)
    return payment_service.get_payments_for_fee(db, fee.id)
