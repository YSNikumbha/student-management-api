from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
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
    statement = select(StudentFee).where(StudentFee.id == fee_id)
    return db.execute(statement).scalar_one_or_none()


def get_student_fees(db: Session, student_id: int) -> list[StudentFee]:
    statement = (
        select(StudentFee)
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
    statement = select(StudentFee)

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

    fee.updated_at = datetime.utcnow()
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


def build_fee_response(db: Session, fee: StudentFee) -> StudentFeeResponse:
    paid_amount = calculate_paid_amount(db, fee.id)
    balance = calculate_balance(fee.total_amount, paid_amount)
    fee_status = calculate_fee_status(fee, paid_amount)

    return StudentFeeResponse(
        id=fee.id,
        student_id=fee.student_id,
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


def get_fee_detail(db: Session, fee: StudentFee) -> StudentFeeResponse:
    return build_fee_response(db, fee)


def get_fee_summary(db: Session) -> dict[str, Decimal | int]:
    fees = get_all_fees(db)
    total_assigned = ZERO_MONEY
    total_collected = ZERO_MONEY
    total_pending = ZERO_MONEY
    counts = {
        FeeStatus.unpaid: 0,
        FeeStatus.partial: 0,
        FeeStatus.paid: 0,
        FeeStatus.overdue: 0,
    }

    for fee in fees:
        paid_amount = calculate_paid_amount(db, fee.id)
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
