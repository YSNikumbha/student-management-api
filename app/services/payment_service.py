from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.schemas.payment import PaymentCreate
from app.services.fee_service import normalize_money


def get_payment_by_id(db: Session, payment_id: int) -> Payment | None:
    statement = select(Payment).where(Payment.id == payment_id)
    return db.execute(statement).scalar_one_or_none()


def get_payments_for_fee(db: Session, fee_id: int) -> list[Payment]:
    statement = (
        select(Payment)
        .where(Payment.student_fee_id == fee_id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
    )
    return list(db.execute(statement).scalars().all())


def calculate_total_paid(db: Session, fee_id: int) -> Decimal:
    statement = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.student_fee_id == fee_id,
    )
    paid_amount = db.execute(statement).scalar_one()
    return normalize_money(paid_amount)


def create_payment(
    db: Session,
    fee_id: int,
    payment_data: PaymentCreate,
    recorded_by: int,
) -> Payment:
    payment = Payment(
        student_fee_id=fee_id,
        amount=payment_data.amount,
        payment_date=payment_data.payment_date,
        payment_method=payment_data.payment_method.value,
        reference_number=payment_data.reference_number,
        notes=payment_data.notes,
        recorded_by=recorded_by,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(db: Session, payment: Payment) -> None:
    db.delete(payment)
    db.commit()
