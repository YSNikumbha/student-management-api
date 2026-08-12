from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.academic_year import AcademicYear
from app.models.batch import Batch
from app.models.course import Course
from app.models.fee_category import FeeCategory
from app.models.fee_installment import FeeInstallment
from app.models.fee_structure import FeeStructure
from app.models.payment import Payment
from app.models.semester import Semester
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.schemas.fee_structure import (
    FeeCategoryCreate,
    FeeCategoryUpdate,
    FeeInstallmentCreate,
    FeeInstallmentResponse,
    FeeInstallmentUpdate,
    FeeStructureAssignRequest,
    FeeStructureCreate,
    FeeStructureResponse,
    FeeStructureUpdate,
    InstallmentStatus,
)
from app.schemas.pagination import get_offset
from app.schemas.student_fee import (
    FeeStatus,
    StudentFeeCreate,
    StudentFeeResponse,
    StudentFeeUpdate,
)

ZERO_MONEY = Decimal("0.00")
MONEY_UNIT = Decimal("0.01")


def normalize_money(value: Decimal | int | float | str | None) -> Decimal:
    if value is None:
        return ZERO_MONEY
    return Decimal(str(value)).quantize(MONEY_UNIT)


def get_fee_by_id(db: Session, fee_id: int) -> StudentFee | None:
    statement = (
        select(StudentFee)
        .options(
            selectinload(StudentFee.student).selectinload(Student.course),
            selectinload(StudentFee.fee_structure),
            selectinload(StudentFee.installments),
        )
        .where(StudentFee.id == fee_id)
    )
    return db.execute(statement).scalar_one_or_none()


def get_student_fees(db: Session, student_id: int) -> list[StudentFee]:
    statement = (
        select(StudentFee)
        .options(selectinload(StudentFee.student))
        .where(StudentFee.student_id == student_id)
        .order_by(StudentFee.due_date.desc(), StudentFee.id.desc())
    )
    return list(db.execute(statement).scalars().all())


def get_all_fees(
    db: Session,
    student_id: int | None = None,
    course_id: int | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
) -> list[StudentFee]:
    statement = select(StudentFee).options(selectinload(StudentFee.student))

    if course_id is not None:
        statement = statement.join(Student, StudentFee.student_id == Student.id).where(
            Student.course_id == course_id,
        )

    if student_id is not None:
        statement = statement.where(StudentFee.student_id == student_id)

    if due_before is not None:
        statement = statement.where(StudentFee.due_date <= due_before)

    if due_after is not None:
        statement = statement.where(StudentFee.due_date >= due_after)

    statement = statement.order_by(StudentFee.due_date.desc(), StudentFee.id.desc())
    return list(db.execute(statement).scalars().all())


def _payment_totals_subquery():
    return (
        select(
            Payment.student_fee_id,
            func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
        )
        .group_by(Payment.student_fee_id)
        .subquery()
    )


def _fee_paid_amount_expression(payment_totals):
    return func.coalesce(payment_totals.c.paid_amount, 0)


def _apply_fee_status_filter(statement, fee_status: FeeStatus, paid_amount):
    balance = StudentFee.total_amount - paid_amount
    current_date = date.today()

    if fee_status == FeeStatus.paid:
        return statement.where(balance <= 0)

    if fee_status == FeeStatus.overdue:
        return statement.where(balance > 0, StudentFee.due_date < current_date)

    if fee_status == FeeStatus.partial:
        return statement.where(
            balance > 0,
            paid_amount > 0,
            StudentFee.due_date >= current_date,
        )

    return statement.where(
        balance > 0,
        paid_amount <= 0,
        StudentFee.due_date >= current_date,
    )


def get_fees_paginated(
    db: Session,
    search: str | None = None,
    student_id: int | None = None,
    course_id: int | None = None,
    status: FeeStatus | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "due_date",
    sort_order: str = "asc",
) -> tuple[list[tuple[StudentFee, Decimal]], int]:
    payment_totals = _payment_totals_subquery()
    paid_amount = _fee_paid_amount_expression(payment_totals)
    statement = (
        select(StudentFee, paid_amount)
        .outerjoin(payment_totals, StudentFee.id == payment_totals.c.student_fee_id)
    )

    if search or course_id is not None:
        statement = statement.join(Student, StudentFee.student_id == Student.id)

    if search:
        search_pattern = f"%{search.lower()}%"
        full_name = func.lower(Student.first_name + " " + Student.last_name)
        statement = statement.where(
            or_(
                func.lower(StudentFee.title).like(search_pattern),
                func.lower(Student.student_code).like(search_pattern),
                func.lower(Student.first_name).like(search_pattern),
                func.lower(Student.last_name).like(search_pattern),
                full_name.like(search_pattern),
            ),
        )

    if student_id is not None:
        statement = statement.where(StudentFee.student_id == student_id)

    if course_id is not None:
        statement = statement.where(Student.course_id == course_id)

    if due_before is not None:
        statement = statement.where(StudentFee.due_date <= due_before)

    if due_after is not None:
        statement = statement.where(StudentFee.due_date >= due_after)

    if status is not None:
        statement = _apply_fee_status_filter(statement, status, paid_amount)

    count_statement = select(func.count()).select_from(
        statement.with_only_columns(StudentFee.id).order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    sort_columns = {
        "due_date": StudentFee.due_date,
        "created_at": StudentFee.created_at,
        "total_amount": StudentFee.total_amount,
    }
    sort_column = sort_columns[sort_by]
    order_column = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    tie_breaker = StudentFee.id.asc() if sort_order == "asc" else StudentFee.id.desc()

    statement = (
        statement.options(selectinload(StudentFee.student))
        .order_by(order_column, tie_breaker)
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )

    return [
        (fee, normalize_money(paid))
        for fee, paid in db.execute(statement).all()
    ], total_items


def create_fee(
    db: Session,
    fee_data: StudentFeeCreate,
    created_by: int,
) -> StudentFee:
    fee = StudentFee(**fee_data.model_dump(), created_by=created_by)
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee


def update_fee(
    db: Session,
    fee: StudentFee,
    fee_data: StudentFeeUpdate,
) -> StudentFee:
    update_data = fee_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fee, field, value)

    fee.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(fee)
    return fee


def delete_fee(db: Session, fee: StudentFee) -> None:
    db.delete(fee)
    db.commit()


def calculate_paid_amount(db: Session, fee_id: int) -> Decimal:
    statement = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.student_fee_id == fee_id,
    )
    paid_amount = db.execute(statement).scalar_one()
    return normalize_money(paid_amount)


def calculate_balance(total_amount: Decimal, paid_amount: Decimal) -> Decimal:
    return normalize_money(total_amount) - normalize_money(paid_amount)


def calculate_fee_status(
    fee: StudentFee,
    paid_amount: Decimal,
    today: date | None = None,
) -> FeeStatus:
    balance = calculate_balance(fee.total_amount, paid_amount)
    current_date = today or date.today()

    if balance <= ZERO_MONEY:
        return FeeStatus.paid

    if current_date > fee.due_date:
        return FeeStatus.overdue

    if paid_amount > ZERO_MONEY:
        return FeeStatus.partial

    return FeeStatus.unpaid


def build_fee_response(
    db: Session,
    fee: StudentFee,
    paid_amount: Decimal | None = None,
) -> StudentFeeResponse:
    paid_amount = paid_amount if paid_amount is not None else calculate_paid_amount(db, fee.id)
    balance = calculate_balance(fee.total_amount, paid_amount)
    fee_status = calculate_fee_status(fee, paid_amount)
    student_name = None
    student_code = None
    course_id = None

    if fee.student is not None:
        student_name = f"{fee.student.first_name} {fee.student.last_name}"
        student_code = fee.student.student_code
        course_id = fee.student.course_id

    return StudentFeeResponse(
        id=fee.id,
        student_id=fee.student_id,
        fee_structure_id=fee.fee_structure_id,
        fee_structure_name=fee.fee_structure.name if fee.fee_structure else None,
        student_code=student_code,
        student_name=student_name,
        course_id=course_id,
        title=fee.title,
        description=fee.description,
        total_amount=normalize_money(fee.total_amount),
        paid_amount=paid_amount,
        balance=balance,
        due_date=fee.due_date,
        status=fee_status,
        created_by=fee.created_by,
        created_at=fee.created_at,
        updated_at=fee.updated_at,
    )


def get_categories_paginated(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[FeeCategory], int]:
    statement = select(FeeCategory)

    if search:
        pattern = f"%{search.lower()}%"
        statement = statement.where(
            or_(
                func.lower(FeeCategory.name).like(pattern),
                func.lower(FeeCategory.description).like(pattern),
            )
        )

    if is_active is not None:
        statement = statement.where(FeeCategory.is_active == is_active)

    total_items = db.execute(
        select(func.count()).select_from(statement.order_by(None).subquery())
    ).scalar_one()
    statement = (
        statement.order_by(FeeCategory.name.asc(), FeeCategory.id.asc())
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )
    return list(db.execute(statement).scalars().all()), total_items


def get_category_by_id(db: Session, category_id: int) -> FeeCategory | None:
    return db.execute(select(FeeCategory).where(FeeCategory.id == category_id)).scalar_one_or_none()


def get_category_by_name(db: Session, name: str) -> FeeCategory | None:
    return db.execute(
        select(FeeCategory).where(func.lower(FeeCategory.name) == name.lower())
    ).scalar_one_or_none()


def create_category(db: Session, category_data: FeeCategoryCreate) -> FeeCategory:
    category = FeeCategory(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session,
    category: FeeCategory,
    category_data: FeeCategoryUpdate,
) -> FeeCategory:
    for field, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def category_has_structures(db: Session, category_id: int) -> bool:
    statement = select(FeeStructure.id).where(FeeStructure.category_id == category_id).limit(1)
    return db.execute(statement).first() is not None


def delete_category(db: Session, category: FeeCategory) -> None:
    db.delete(category)
    db.commit()


def _structure_options():
    return (
        selectinload(FeeStructure.course),
        selectinload(FeeStructure.academic_year),
        selectinload(FeeStructure.semester),
        selectinload(FeeStructure.category),
        selectinload(FeeStructure.student_fees),
    )


def get_structure_by_id(db: Session, structure_id: int) -> FeeStructure | None:
    statement = (
        select(FeeStructure)
        .options(*_structure_options())
        .where(FeeStructure.id == structure_id)
    )
    return db.execute(statement).scalar_one_or_none()


def get_structures_paginated(
    db: Session,
    *,
    search: str | None = None,
    course_id: int | None = None,
    academic_year_id: int | None = None,
    semester_id: int | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[FeeStructure], int]:
    statement = select(FeeStructure).options(*_structure_options())

    if search:
        pattern = f"%{search.lower()}%"
        statement = statement.where(func.lower(FeeStructure.name).like(pattern))

    if course_id is not None:
        statement = statement.where(FeeStructure.course_id == course_id)

    if academic_year_id is not None:
        statement = statement.where(FeeStructure.academic_year_id == academic_year_id)

    if semester_id is not None:
        statement = statement.where(FeeStructure.semester_id == semester_id)

    if category_id is not None:
        statement = statement.where(FeeStructure.category_id == category_id)

    if is_active is not None:
        statement = statement.where(FeeStructure.is_active == is_active)

    total_items = db.execute(
        select(func.count()).select_from(
            statement.with_only_columns(FeeStructure.id).order_by(None).subquery()
        )
    ).scalar_one()
    statement = (
        statement.order_by(FeeStructure.created_at.desc(), FeeStructure.id.desc())
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )
    return list(db.execute(statement).scalars().all()), total_items


def create_structure(db: Session, structure_data: FeeStructureCreate) -> FeeStructure:
    structure = FeeStructure(**structure_data.model_dump())
    db.add(structure)
    db.commit()
    db.refresh(structure)
    return get_structure_by_id(db, structure.id) or structure


def update_structure(
    db: Session,
    structure: FeeStructure,
    structure_data: FeeStructureUpdate,
) -> FeeStructure:
    for field, value in structure_data.model_dump(exclude_unset=True).items():
        setattr(structure, field, value)
    db.commit()
    db.refresh(structure)
    return get_structure_by_id(db, structure.id) or structure


def structure_has_assignments(db: Session, structure_id: int) -> bool:
    statement = select(StudentFee.id).where(StudentFee.fee_structure_id == structure_id).limit(1)
    return db.execute(statement).first() is not None


def delete_structure(db: Session, structure: FeeStructure) -> None:
    db.delete(structure)
    db.commit()


def build_structure_response(structure: FeeStructure) -> FeeStructureResponse:
    return FeeStructureResponse(
        id=structure.id,
        name=structure.name,
        course_id=structure.course_id,
        course_name=structure.course.name if structure.course else None,
        academic_year_id=structure.academic_year_id,
        academic_year_name=structure.academic_year.name if structure.academic_year else None,
        semester_id=structure.semester_id,
        semester_name=structure.semester.name if structure.semester else None,
        category_id=structure.category_id,
        category_name=structure.category.name if structure.category else None,
        total_amount=normalize_money(structure.total_amount),
        description=structure.description,
        is_active=structure.is_active,
        created_at=structure.created_at,
        assignment_count=len(structure.student_fees),
    )


def _installment_paid_amount_expression():
    return (
        select(
            Payment.fee_installment_id,
            func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
        )
        .where(Payment.fee_installment_id.is_not(None))
        .group_by(Payment.fee_installment_id)
        .subquery()
    )


def calculate_installment_paid_amount(db: Session, installment_id: int) -> Decimal:
    statement = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.fee_installment_id == installment_id,
    )
    return normalize_money(db.execute(statement).scalar_one())


def calculate_installment_status(
    installment: FeeInstallment,
    paid_amount: Decimal,
    today: date | None = None,
) -> InstallmentStatus:
    balance = normalize_money(installment.amount) - normalize_money(paid_amount)
    current_date = today or date.today()
    if balance <= ZERO_MONEY:
        return InstallmentStatus.paid
    if paid_amount > ZERO_MONEY:
        return InstallmentStatus.partial
    if current_date > installment.due_date:
        return InstallmentStatus.overdue
    return InstallmentStatus.unpaid


def build_installment_response(
    db: Session,
    installment: FeeInstallment,
    paid_amount: Decimal | None = None,
) -> FeeInstallmentResponse:
    paid = paid_amount if paid_amount is not None else calculate_installment_paid_amount(db, installment.id)
    balance = normalize_money(installment.amount) - normalize_money(paid)
    return FeeInstallmentResponse(
        id=installment.id,
        student_fee_id=installment.student_fee_id,
        title=installment.title,
        amount=normalize_money(installment.amount),
        due_date=installment.due_date,
        sequence_number=installment.sequence_number,
        paid_amount=paid,
        balance=balance if balance > ZERO_MONEY else ZERO_MONEY,
        status=calculate_installment_status(installment, paid),
    )


def get_installment_by_id(db: Session, installment_id: int) -> FeeInstallment | None:
    statement = select(FeeInstallment).where(FeeInstallment.id == installment_id)
    return db.execute(statement).scalar_one_or_none()


def get_installments_for_fee(db: Session, fee_id: int) -> list[FeeInstallment]:
    statement = (
        select(FeeInstallment)
        .where(FeeInstallment.student_fee_id == fee_id)
        .order_by(FeeInstallment.sequence_number.asc(), FeeInstallment.id.asc())
    )
    return list(db.execute(statement).scalars().all())


def _installment_total(
    db: Session,
    fee_id: int,
    *,
    exclude_installment_id: int | None = None,
) -> Decimal:
    statement = select(func.coalesce(func.sum(FeeInstallment.amount), 0)).where(
        FeeInstallment.student_fee_id == fee_id,
    )
    if exclude_installment_id is not None:
        statement = statement.where(FeeInstallment.id != exclude_installment_id)
    return normalize_money(db.execute(statement).scalar_one())


def validate_installment_total(
    db: Session,
    fee: StudentFee,
    new_amount: Decimal,
    *,
    exclude_installment_id: int | None = None,
) -> None:
    total = _installment_total(db, fee.id, exclude_installment_id=exclude_installment_id)
    if total + normalize_money(new_amount) > normalize_money(fee.total_amount):
        raise ValueError("Installment total cannot exceed fee amount")


def create_installment(
    db: Session,
    fee: StudentFee,
    installment_data: FeeInstallmentCreate,
) -> FeeInstallment:
    validate_installment_total(db, fee, installment_data.amount)
    installment = FeeInstallment(
        student_fee_id=fee.id,
        **installment_data.model_dump(),
    )
    db.add(installment)
    db.commit()
    db.refresh(installment)
    return installment


def update_installment(
    db: Session,
    fee: StudentFee,
    installment: FeeInstallment,
    installment_data: FeeInstallmentUpdate,
) -> FeeInstallment:
    update_data = installment_data.model_dump(exclude_unset=True)
    amount = update_data.get("amount", installment.amount)
    validate_installment_total(
        db,
        fee,
        amount,
        exclude_installment_id=installment.id,
    )
    for field, value in update_data.items():
        setattr(installment, field, value)
    db.commit()
    db.refresh(installment)
    return installment


def installment_has_payments(db: Session, installment_id: int) -> bool:
    statement = select(Payment.id).where(Payment.fee_installment_id == installment_id).limit(1)
    return db.execute(statement).first() is not None


def delete_installment(db: Session, installment: FeeInstallment) -> None:
    db.delete(installment)
    db.commit()


def _create_installments_for_fee(
    db: Session,
    fee: StudentFee,
    installments: list[FeeInstallmentCreate],
) -> None:
    total = sum((normalize_money(item.amount) for item in installments), ZERO_MONEY)
    if total > normalize_money(fee.total_amount):
        raise ValueError("Installment total cannot exceed fee amount")

    for item in installments:
        db.add(
            FeeInstallment(
                student_fee_id=fee.id,
                **item.model_dump(),
            )
        )


def assign_structure(
    db: Session,
    structure: FeeStructure,
    assignment_data: FeeStructureAssignRequest,
    *,
    created_by: int,
) -> tuple[int, int, list[int]]:
    if assignment_data.student_id is not None:
        students = list(
            db.execute(
                select(Student).where(Student.id == assignment_data.student_id)
            ).scalars().all()
        )
    else:
        students = list(
            db.execute(
                select(Student)
                .where(Student.batch_id == assignment_data.batch_id)
                .order_by(Student.id.asc())
            ).scalars().all()
        )

    created_ids: list[int] = []
    skipped = 0

    try:
        for student in students:
            exists = db.execute(
                select(StudentFee.id).where(
                    StudentFee.student_id == student.id,
                    StudentFee.fee_structure_id == structure.id,
                )
            ).first()
            if exists is not None:
                skipped += 1
                continue

            fee = StudentFee(
                student_id=student.id,
                fee_structure_id=structure.id,
                title=structure.name,
                description=structure.description,
                total_amount=structure.total_amount,
                due_date=assignment_data.due_date,
                created_by=created_by,
            )
            db.add(fee)
            db.flush()
            _create_installments_for_fee(db, fee, assignment_data.installments)
            created_ids.append(fee.id)

        db.commit()
        return len(created_ids), skipped, created_ids
    except Exception:
        db.rollback()
        raise


def get_course(db: Session, course_id: int) -> Course | None:
    return db.execute(select(Course).where(Course.id == course_id)).scalar_one_or_none()


def get_academic_year(db: Session, academic_year_id: int) -> AcademicYear | None:
    return db.execute(
        select(AcademicYear).where(AcademicYear.id == academic_year_id)
    ).scalar_one_or_none()


def get_semester(db: Session, semester_id: int) -> Semester | None:
    return db.execute(select(Semester).where(Semester.id == semester_id)).scalar_one_or_none()


def get_batch(db: Session, batch_id: int) -> Batch | None:
    return db.execute(select(Batch).where(Batch.id == batch_id)).scalar_one_or_none()


def get_fee_detail(db: Session, fee: StudentFee) -> StudentFeeResponse:
    return build_fee_response(db, fee)


def get_fee_summary(db: Session) -> dict[str, Decimal | int]:
    payment_totals = _payment_totals_subquery()
    paid_amount_expression = _fee_paid_amount_expression(payment_totals)
    statement = (
        select(StudentFee, paid_amount_expression)
        .outerjoin(payment_totals, StudentFee.id == payment_totals.c.student_fee_id)
    )
    fee_rows = db.execute(statement).all()
    total_assigned = ZERO_MONEY
    total_collected = ZERO_MONEY
    total_pending = ZERO_MONEY
    counts = {
        FeeStatus.unpaid: 0,
        FeeStatus.partial: 0,
        FeeStatus.paid: 0,
        FeeStatus.overdue: 0,
    }

    for fee, paid_amount in fee_rows:
        paid_amount = normalize_money(paid_amount)
        balance = calculate_balance(fee.total_amount, paid_amount)
        fee_status = calculate_fee_status(fee, paid_amount)

        total_assigned += normalize_money(fee.total_amount)
        total_collected += paid_amount
        total_pending += balance if balance > ZERO_MONEY else ZERO_MONEY
        counts[fee_status] += 1

    return {
        "total_assigned": normalize_money(total_assigned),
        "total_collected": normalize_money(total_collected),
        "total_pending": normalize_money(total_pending),
        "unpaid_count": counts[FeeStatus.unpaid],
        "partial_count": counts[FeeStatus.partial],
        "paid_count": counts[FeeStatus.paid],
        "overdue_count": counts[FeeStatus.overdue],
    }


def fee_has_payments(db: Session, fee_id: int) -> bool:
    statement = select(Payment.id).where(Payment.student_fee_id == fee_id).limit(1)
    return db.execute(statement).first() is not None


def student_has_fees(db: Session, student_id: int) -> bool:
    statement = select(StudentFee.id).where(StudentFee.student_id == student_id).limit(1)
    return db.execute(statement).first() is not None
