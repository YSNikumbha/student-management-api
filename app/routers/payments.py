from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_fee_manager
from app.models.user import User
from app.schemas.payment import PaymentReceiptResponse
from app.services import audit_service, payment_service

router = APIRouter(
    prefix="/payments",
    tags=["Fees"],
)


def _get_payment_or_404(db: Session, payment_id: int):
    payment = payment_service.get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment


def _build_receipt_pdf(receipt: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Student Management System", styles["Title"]),
        Paragraph("Payment Receipt", styles["Heading2"]),
        Spacer(1, 12),
    ]
    rows = [
        ["Receipt Number", receipt["receipt_number"] or ""],
        ["Student", receipt["student_name"]],
        ["Student Code", receipt["student_code"]],
        ["Course", receipt["course_name"] or ""],
        ["Fee", receipt["fee_title"]],
        ["Amount Paid", f"{receipt['amount_paid']:.2f}"],
        ["Payment Method", str(receipt["payment_method"])],
        ["Reference", receipt["reference_number"] or ""],
        ["Payment Date", receipt["payment_date"].isoformat()],
        ["Balance", f"{receipt['balance']:.2f}"],
        ["Recorded By", receipt["recorded_by_name"] or ""],
    ]
    table = Table(rows, colWidths=[150, 330])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/{payment_id}/receipt", response_model=PaymentReceiptResponse)
def get_payment_receipt(
    payment_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> PaymentReceiptResponse:
    payment = _get_payment_or_404(db, payment_id)
    return PaymentReceiptResponse(**payment_service.build_receipt_data(db, payment))


@router.get("/{payment_id}/receipt/pdf")
def get_payment_receipt_pdf(
    payment_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Response:
    payment = _get_payment_or_404(db, payment_id)
    receipt = payment_service.build_receipt_data(db, payment)
    pdf_bytes = _build_receipt_pdf(receipt)
    filename = f"{receipt['receipt_number'] or f'payment_{payment_id}'}_receipt.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_payment(
    payment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_fee_manager),
) -> Response:
    payment = _get_payment_or_404(db, payment_id)

    metadata = {
        "student_fee_id": payment.student_fee_id,
        "amount": payment.amount,
        "payment_date": payment.payment_date,
        "receipt_number": getattr(payment, "receipt_number", None),
    }
    try:
        payment_service.delete_payment(db, payment)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment could not be deleted",
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="payment_deleted",
        entity_type="payment",
        entity_id=payment_id,
        description="Payment deleted",
        metadata_json=metadata,
        ip_address=audit_service.get_request_ip(request),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
