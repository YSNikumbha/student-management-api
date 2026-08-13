from datetime import date

from sqlalchemy import func, select

from app.models.academic_performance import Assessment, StudentResult
from app.models.payment import Payment
from app.models.student_fee import StudentFee
from scripts.seed_demo_data import seed


def test_demo_seed_is_idempotent(test_db) -> None:
    first = seed(test_db, student_count=8, attendance_days=10)
    second = seed(test_db, student_count=8, attendance_days=10)
    assert first["students"]["inserted"] > 0
    assert second["students"]["inserted"] == 0
    assert second["students"]["skipped"] >= first["students"]["inserted"]


def test_demo_seed_adds_current_period_report_data(test_db) -> None:
    today = date.today()
    seed(test_db, student_count=8, attendance_days=10)

    assessment_ids = list(
        test_db.execute(
            select(Assessment.id).where(
                Assessment.name.like(f"Demo Current Month%{today:%b %Y}%"),
                func.extract("year", Assessment.date) == today.year,
                func.extract("month", Assessment.date) == today.month,
            )
        ).scalars().all()
    )
    assert assessment_ids

    result_count = test_db.execute(
        select(func.count(StudentResult.id)).where(StudentResult.assessment_id.in_(assessment_ids))
    ).scalar_one()
    assert result_count > 0

    current_fee_count = test_db.execute(
        select(func.count(StudentFee.id)).where(
            StudentFee.invoice_number.like(f"DEMO-INV-CUR-%-{today:%Y%m}"),
            StudentFee.due_date == today,
        )
    ).scalar_one()
    assert current_fee_count == 8

    current_payment_count = test_db.execute(
        select(func.count(Payment.id)).where(
            Payment.receipt_number.like(f"DEMO-RCPT-CUR-%-{today:%Y%m}"),
            Payment.payment_date == today,
        )
    ).scalar_one()
    assert current_payment_count > 0
