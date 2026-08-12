from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.user import User
from app.schemas.payment import PaymentCreate
from app.services.fee_service import normalize_money


def get_payment_by_id(db: Session, payment_id: int) -> Payment | None:
    statement = (
        select(Payment)
        .options(
            selectinload(Payment.student_fee)
            .selectinload(StudentFee.student)
            .selectinload(Student.course),
            selectinload(Payment.recorder),
            selectinload(Payment.fee_installment),
        )
        .where(Payment.id == payment_id)
    )
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


def generate_receipt_number(db: Session, payment_year: int) -> str:
    prefix = f"RCPT-{payment_year}-"
    count = db.execute(
        select(func.count(Payment.id)).where(Payment.receipt_number.like(f"{prefix}%"))
    ).scalar_one()
    next_number = int(count) + 1

    while True:
        receipt_number = f"{prefix}{next_number:06d}"
        existing = db.execute(
            select(Payment.id).where(Payment.receipt_number == receipt_number)
        ).first()
        if existing is None:
            return receipt_number
        next_number += 1


def create_payment(
    db: Session,
    fee_id: int,
    payment_data: PaymentCreate,
    recorded_by: int,
) -> Payment:
    receipt_number = generate_receipt_number(db, payment_data.payment_date.year)
    payment = Payment(
        student_fee_id=fee_id,
        fee_installment_id=payment_data.fee_installment_id,
        receipt_number=receipt_number,
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


def build_receipt_data(db: Session, payment: Payment) -> dict:
    fee = payment.student_fee
    student = fee.student if fee else None
    course = student.course if student and student.course else None
    paid_amount = calculate_total_paid(db, payment.student_fee_id)
    balance = normalize_money(fee.total_amount if fee else 0) - normalize_money(paid_amount)

    return {
        "payment_id": payment.id,
        "receipt_number": payment.receipt_number,
        "student_name": f"{student.first_name} {student.last_name}" if student else "",
        "student_code": student.student_code if student else "",
        "course_name": course.name if course else None,
        "fee_title": fee.title if fee else "",
        "amount_paid": normalize_money(payment.amount),
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "payment_date": payment.payment_date,
        "balance": balance if balance > Decimal("0.00") else Decimal("0.00"),
        "recorded_by_name": payment.recorder.name if isinstance(payment.recorder, User) else None,
        "created_at": payment.created_at,
    }
