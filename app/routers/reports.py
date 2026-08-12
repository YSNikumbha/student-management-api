import csv
from datetime import date
from io import BytesIO, StringIO
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_fee_report_reader, require_general_report_reader
from app.schemas.report import ReportFilters
from app.services import report_service

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def _validate_date_range(start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be before end_date",
        )


@router.get(
    "/students",
    dependencies=[Depends(require_general_report_reader)],
)
def get_student_report(
    search: str | None = None,
    course_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    created_from: date | None = None,
    created_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    _validate_date_range(created_from, created_to)
    items, total_items = report_service.get_student_report(
        db,
        search=search,
        course_id=course_id,
        status=report_status,
        created_from=created_from,
        created_to=created_to,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "total": total_items,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/attendance",
    dependencies=[Depends(require_general_report_reader)],
)
def get_attendance_report(
    course_id: int | None = None,
    student_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    detail: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    _validate_date_range(start_date, end_date)
    items, total_items = report_service.get_attendance_report(
        db,
        course_id=course_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        detail=detail,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "total": total_items,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/fees",
    dependencies=[Depends(require_fee_report_reader)],
)
def get_fee_report(
    student_id: int | None = None,
    course_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    due_from: date | None = None,
    due_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    _validate_date_range(due_from, due_to)
    items, total_items = report_service.get_fee_report(
        db,
        student_id=student_id,
        course_id=course_id,
        status=report_status,
        due_from=due_from,
        due_to=due_to,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "total": total_items,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/courses",
    dependencies=[Depends(require_general_report_reader)],
)
def get_course_report(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    items, total_items = report_service.get_course_report(
        db,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "total": total_items,
        "page": page,
        "page_size": page_size,
    }


def _generate_student_csv(items: list[dict]) -> str:
    return _write_csv(
        [
            "student_id",
            "student_code",
            "full_name",
            "email",
            "phone",
            "course_id",
            "course_name",
            "status",
            "date_of_birth",
            "created_at",
        ],
        [
            [
                item["student_id"],
                item["student_code"],
                item["full_name"],
                item["email"],
                item["phone"] or "",
                item["course_id"] or "",
                item["course_name"] or "",
                item["status"],
                item["date_of_birth"] or "",
                item["created_at"],
            ]
            for item in items
        ],
    )


def _generate_attendance_csv(items: list[dict], detailed: bool = False) -> str:
    if detailed:
        return _write_csv(
            ["date", "student_code", "student_name", "course_name", "status", "remarks", "marked_by"],
            [
                [
                    item["date"] or "",
                    item["student_code"],
                    item["student_name"],
                    item["course_name"] or "",
                    item["status"],
                    item["remarks"] or "",
                    item["marked_by"],
                ]
                for item in items
            ],
        )

    return _write_csv(
        [
            "student_id",
            "student_code",
            "student_name",
            "course_name",
            "total_marked_days",
            "present_days",
            "absent_days",
            "late_days",
            "attendance_percentage",
        ],
        [
            [
                item["student_id"],
                item["student_code"],
                item["student_name"],
                item["course_name"] or "",
                item["total_marked_days"],
                item["present_days"],
                item["absent_days"],
                item["late_days"],
                item["attendance_percentage"],
            ]
            for item in items
        ],
    )


def _generate_fee_csv(items: list[dict]) -> str:
    return _write_csv(
        [
            "student_id",
            "student_code",
            "student_name",
            "course_name",
            "title",
            "total_amount",
            "paid_amount",
            "balance",
            "due_date",
            "status",
        ],
        [
            [
                item["student_id"],
                item["student_code"],
                item["student_name"],
                item["course_name"] or "",
                item["title"],
                item["total_amount"],
                item["paid_amount"],
                item["balance"],
                item["due_date"],
                item["status"],
            ]
            for item in items
        ],
    )


def _generate_course_csv(items: list[dict]) -> str:
    return _write_csv(
        [
            "course_id",
            "course_code",
            "course_name",
            "is_active",
            "student_count",
            "active_student_count",
            "average_attendance_percentage",
            "total_fees_assigned",
            "total_fees_collected",
            "total_fees_pending",
        ],
        [
            [
                item["course_id"],
                item["course_code"],
                item["course_name"],
                item["is_active"],
                item["student_count"],
                item["active_student_count"],
                item["average_attendance_percentage"] or "",
                item["total_fees_assigned"],
                item["total_fees_collected"],
                item["total_fees_pending"],
            ]
            for item in items
        ],
    )


def _write_csv(headers: list[str], rows: list[list[object]]) -> str:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()


@router.get(
    "/students/export/csv",
    dependencies=[Depends(require_general_report_reader)],
)
def export_students_csv(
    search: str | None = None,
    course_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    created_from: date | None = None,
    created_to: date | None = None,
    db: Session = Depends(get_db),
) -> Response:
    _validate_date_range(created_from, created_to)
    items, _ = report_service.get_student_report(
        db,
        search=search,
        course_id=course_id,
        status=report_status,
        created_from=created_from,
        created_to=created_to,
        page=1,
        page_size=500,
    )
    csv_content = _generate_student_csv([item.model_dump(mode="json") for item in items])
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=students_report_{date.today()}.csv"},
    )


@router.get(
    "/attendance/export/csv",
    dependencies=[Depends(require_general_report_reader)],
)
def export_attendance_csv(
    course_id: int | None = None,
    student_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    detail: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Response:
    _validate_date_range(start_date, end_date)
    items, _ = report_service.get_attendance_report(
        db,
        course_id=course_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        detail=detail,
        page=1,
        page_size=500,
    )
    csv_content = _generate_attendance_csv([item.model_dump(mode="json") for item in items], detailed=detail)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_report_{date.today()}.csv"},
    )


@router.get(
    "/fees/export/csv",
    dependencies=[Depends(require_fee_report_reader)],
)
def export_fees_csv(
    student_id: int | None = None,
    course_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    due_from: date | None = None,
    due_to: date | None = None,
    db: Session = Depends(get_db),
) -> Response:
    _validate_date_range(due_from, due_to)
    items, _ = report_service.get_fee_report(
        db,
        student_id=student_id,
        course_id=course_id,
        status=report_status,
        due_from=due_from,
        due_to=due_to,
        page=1,
        page_size=500,
    )
    csv_content = _generate_fee_csv([item.model_dump(mode="json") for item in items])
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=fees_report_{date.today()}.csv"},
    )


@router.get(
    "/courses/export/csv",
    dependencies=[Depends(require_general_report_reader)],
)
def export_courses_csv(
    search: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
) -> Response:
    items, _ = report_service.get_course_report(
        db,
        search=search,
        is_active=is_active,
        page=1,
        page_size=500,
    )
    csv_content = _generate_course_csv([item.model_dump(mode="json") for item in items])
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=courses_report_{date.today()}.csv"},
    )


def _build_pdf(title: str, headers: list[str], rows: list[list[str]]) -> bytes:
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Student Management System", styles["Title"]))
    elements.append(Paragraph(title, styles["Heading2"]))
    elements.append(Paragraph(f"Generated: {date.today().isoformat()}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    table_data = [headers] + rows
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


@router.get(
    "/students/export/pdf",
    dependencies=[Depends(require_general_report_reader)],
)
def export_students_pdf(
    search: str | None = None,
    course_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    created_from: date | None = None,
    created_to: date | None = None,
    db: Session = Depends(get_db),
) -> Response:
    _validate_date_range(created_from, created_to)
    items, _ = report_service.get_student_report(
        db,
        search=search,
        course_id=course_id,
        status=report_status,
        created_from=created_from,
        created_to=created_to,
        page=1,
        page_size=500,
    )
    headers = ["ID", "Code", "Full Name", "Email", "Phone", "Course", "Status", "DOB", "Created"]
    rows = [
        [
            str(item.student_id),
            item.student_code,
            item.full_name,
            item.email,
            item.phone or "",
            item.course_name or "",
            item.status,
            item.date_of_birth.isoformat() if item.date_of_birth else "",
            item.created_at.isoformat(),
        ]
        for item in items
    ]
    pdf_bytes = _build_pdf("Student Report", headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=students_report_{date.today()}.pdf"},
    )


@router.get(
    "/attendance/export/pdf",
    dependencies=[Depends(require_general_report_reader)],
)
def export_attendance_pdf(
    course_id: int | None = None,
    student_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    detail: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Response:
    _validate_date_range(start_date, end_date)
    items, _ = report_service.get_attendance_report(
        db,
        course_id=course_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        detail=detail,
        page=1,
        page_size=500,
    )
    if detail:
        headers = ["Date", "Student Code", "Student Name", "Course", "Status", "Remarks", "Marked By"]
        rows = [
            [
                item.date.isoformat() if item.date else "",
                item.student_code,
                item.student_name,
                item.course_name or "",
                item.status,
                item.remarks or "",
                str(item.marked_by),
            ]
            for item in items
        ]
    else:
        headers = ["Student ID", "Code", "Name", "Course", "Total", "Present", "Absent", "Late", "%"]
        rows = [
            [
                str(item.student_id),
                item.student_code,
                item.student_name,
                item.course_name or "",
                str(item.total_marked_days),
                str(item.present_days),
                str(item.absent_days),
                str(item.late_days),
                f"{item.attendance_percentage}%",
            ]
            for item in items
        ]
    pdf_bytes = _build_pdf("Attendance Report", headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=attendance_report_{date.today()}.pdf"},
    )


@router.get(
    "/fees/export/pdf",
    dependencies=[Depends(require_fee_report_reader)],
)
def export_fees_pdf(
    student_id: int | None = None,
    course_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    due_from: date | None = None,
    due_to: date | None = None,
    db: Session = Depends(get_db),
) -> Response:
    _validate_date_range(due_from, due_to)
    items, _ = report_service.get_fee_report(
        db,
        student_id=student_id,
        course_id=course_id,
        status=report_status,
        due_from=due_from,
        due_to=due_to,
        page=1,
        page_size=500,
    )
    headers = ["Student ID", "Code", "Name", "Course", "Title", "Total", "Paid", "Balance", "Due Date", "Status"]
    rows = [
        [
            str(item.student_id),
            item.student_code,
            item.student_name,
            item.course_name or "",
            item.title,
            f"{item.total_amount:.2f}",
            f"{item.paid_amount:.2f}",
            f"{item.balance:.2f}",
            item.due_date.isoformat(),
            item.status,
        ]
        for item in items
    ]
    pdf_bytes = _build_pdf("Fee Report", headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=fees_report_{date.today()}.pdf"},
    )


@router.get(
    "/courses/export/pdf",
    dependencies=[Depends(require_general_report_reader)],
)
def export_courses_pdf(
    search: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
) -> Response:
    items, _ = report_service.get_course_report(
        db,
        search=search,
        is_active=is_active,
        page=1,
        page_size=500,
    )
    headers = [
        "ID",
        "Code",
        "Name",
        "Active",
        "Students",
        "Active Students",
        "Avg Attendance %",
        "Fees Assigned",
        "Fees Collected",
        "Fees Pending",
    ]
    rows = [
        [
            str(item.course_id),
            item.course_code,
            item.course_name,
            str(item.is_active),
            str(item.student_count),
            str(item.active_student_count),
            f"{item.average_attendance_percentage:.2f}%" if item.average_attendance_percentage is not None else "",
            f"{item.total_fees_assigned:.2f}",
            f"{item.total_fees_collected:.2f}",
            f"{item.total_fees_pending:.2f}",
        ]
        for item in items
    ]
    pdf_bytes = _build_pdf("Course Report", headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=courses_report_{date.today()}.pdf"},
    )
