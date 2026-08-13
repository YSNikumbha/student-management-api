import csv
from datetime import date
from io import BytesIO, StringIO
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_fee_report_reader, require_general_report_reader, require_permission
from app.models.batch import Batch
from app.models.fee_category import FeeCategory
from app.models.student import Student
from app.models.subject import Subject
from app.schemas.report import ReportFilter, ReportPeriod
from app.services import academic_performance_service, report_service

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


def _reject(message: str, *, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY) -> None:
    raise HTTPException(status_code=status_code, detail=message)


def _validate_period_filter(filters: ReportFilter) -> None:
    period = filters.period
    if period is None:
        _validate_date_range(filters.start_date, filters.end_date)
        return

    if filters.start_date is not None or filters.end_date is not None:
        _reject("start_date/end_date cannot be combined with period filters")

    if period == ReportPeriod.daily:
        if filters.date is None:
            _reject("date is required when period=daily")
        if filters.month is not None or filters.year is not None or filters.from_date is not None or filters.to_date is not None:
            _reject("Daily reports only accept date")

    if period == ReportPeriod.monthly:
        if filters.year is None:
            _reject("year is required when period=monthly")
        if filters.month is None:
            _reject("month is required when period=monthly")
        if filters.date is not None or filters.from_date is not None or filters.to_date is not None:
            _reject("Monthly reports only accept year and month")

    if period == ReportPeriod.yearly:
        if filters.year is None:
            _reject("year is required when period=yearly")
        if filters.date is not None or filters.month is not None or filters.from_date is not None or filters.to_date is not None:
            _reject("Yearly reports only accept year")

    if period == ReportPeriod.custom:
        if filters.from_date is None:
            _reject("from_date is required when period=custom")
        if filters.to_date is None:
            _reject("to_date is required when period=custom")
        if filters.date is not None or filters.month is not None or filters.year is not None:
            _reject("Custom reports only accept from_date and to_date")
        if filters.from_date and filters.to_date and filters.from_date > filters.to_date:
            _reject("from_date must be before or equal to to_date")


def _validate_class_student_filters(db: Session, filters: ReportFilter) -> None:
    if filters.class_id is not None and db.get(Batch, filters.class_id) is None:
        _reject("Class not found")

    student = None
    if filters.student_id is not None:
        student = db.get(Student, filters.student_id)
        if student is None:
            _reject("Student not found")

    if filters.class_id is not None and student is not None and student.batch_id != filters.class_id:
        _reject("Student does not belong to selected class", status_code=status.HTTP_409_CONFLICT)


def report_filter_dependency(
    period: ReportPeriod | None = Query(default=None),
    report_date: date | None = Query(default=None, alias="date"),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=1900, le=2200),
    from_date: date | None = None,
    to_date: date | None = None,
    class_id: int | None = None,
    student_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
) -> ReportFilter:
    filters = ReportFilter(
        period=period,
        date=report_date,
        month=month,
        year=year,
        from_date=from_date,
        to_date=to_date,
        class_id=class_id,
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
    )
    _validate_period_filter(filters)
    _validate_class_student_filters(db, filters)
    return filters


def _validate_subject(db: Session, subject_id: int | None) -> None:
    if subject_id is not None and db.get(Subject, subject_id) is None:
        _reject("Subject not found")


def _validate_fee_category(db: Session, category_id: int | None) -> None:
    if category_id is not None and db.get(FeeCategory, category_id) is None:
        _reject("Fee category not found")


def _filters_payload(filters: ReportFilter, start_date: date | None, end_date: date | None) -> dict:
    payload = filters.model_dump(mode="json")
    payload["start_date"] = start_date.isoformat() if start_date else None
    payload["end_date"] = end_date.isoformat() if end_date else None
    payload["active_period"] = filters.active_period
    return payload


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
    status_filter: str | None = Query(default=None, alias="status"),
    filters: ReportFilter = Depends(report_filter_dependency),
    detail: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    start_date, end_date = filters.effective_range()
    items, total_items = report_service.get_attendance_report(
        db,
        course_id=course_id,
        class_id=filters.class_id,
        student_id=filters.student_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        detail=detail,
        page=page,
        page_size=page_size,
    )
    summary = report_service.get_attendance_summary(
        db,
        course_id=course_id,
        class_id=filters.class_id,
        student_id=filters.student_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "summary": summary.model_dump(mode="json"),
        "filters": _filters_payload(filters, start_date, end_date),
        "total": total_items,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/fees",
    dependencies=[Depends(require_fee_report_reader)],
)
def get_fee_report(
    course_id: int | None = None,
    category_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    due_from: date | None = None,
    due_to: date | None = None,
    filters: ReportFilter = Depends(report_filter_dependency),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    _validate_fee_category(db, category_id)
    period_start, period_end = filters.effective_range()
    effective_due_from = period_start or due_from
    effective_due_to = period_end or due_to
    _validate_date_range(effective_due_from, effective_due_to)
    items, total_items = report_service.get_fee_report(
        db,
        student_id=filters.student_id,
        course_id=course_id,
        class_id=filters.class_id,
        category_id=category_id,
        status=report_status,
        due_from=effective_due_from,
        due_to=effective_due_to,
        page=page,
        page_size=page_size,
    )
    summary = report_service.get_financial_summary(
        db,
        student_id=filters.student_id,
        course_id=course_id,
        class_id=filters.class_id,
        category_id=category_id,
        status=report_status,
        due_from=effective_due_from,
        due_to=effective_due_to,
        payment_from=effective_due_from,
        payment_to=effective_due_to,
    )
    return {
        "items": [item.model_dump(mode="json") for item in items],
        "summary": summary.model_dump(mode="json"),
        "filters": _filters_payload(filters, effective_due_from, effective_due_to),
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


@router.get(
    "/academic",
    dependencies=[Depends(require_general_report_reader)],
)
def get_academic_report(
    filters: ReportFilter = Depends(report_filter_dependency),
    subject_id: int | None = None,
    top_n: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
) -> dict:
    _validate_subject(db, subject_id)
    if top_n not in {5, 10, 20}:
        _reject("top_n must be one of 5, 10, or 20")
    start_date, end_date = filters.effective_range()
    data = academic_performance_service.get_academic_report(
        db,
        start_date=start_date,
        end_date=end_date,
        class_id=filters.class_id,
        student_id=filters.student_id,
        subject_id=subject_id,
        top_n=top_n,
    )
    data["filters"] = {
        **_filters_payload(filters, start_date, end_date),
        "subject_id": subject_id,
        "top_n": top_n,
    }
    return data


@router.get(
    "/top-performers",
    dependencies=[Depends(require_general_report_reader)],
)
def get_top_performers_report(
    filters: ReportFilter = Depends(report_filter_dependency),
    subject_id: int | None = None,
    top_n: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
) -> dict:
    _validate_subject(db, subject_id)
    if top_n not in {5, 10, 20}:
        _reject("top_n must be one of 5, 10, or 20")
    start_date, end_date = filters.effective_range()
    data = academic_performance_service.get_academic_report(
        db,
        start_date=start_date,
        end_date=end_date,
        class_id=filters.class_id,
        student_id=filters.student_id,
        subject_id=subject_id,
        top_n=top_n,
    )
    return {
        "items": data["top_students"],
        "total": len(data["top_students"]),
        "filters": {
            **_filters_payload(filters, start_date, end_date),
            "subject_id": subject_id,
            "top_n": top_n,
        },
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
            "excused_days",
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
                item.get("excused_days", 0),
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
            "fee_category",
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
                item.get("fee_category") or "",
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


def _academic_data(
    db: Session,
    filters: ReportFilter,
    subject_id: int | None,
    top_n: int,
) -> dict:
    _validate_subject(db, subject_id)
    if top_n not in {5, 10, 20}:
        _reject("top_n must be one of 5, 10, or 20")
    start_date, end_date = filters.effective_range()
    return academic_performance_service.get_academic_report(
        db,
        start_date=start_date,
        end_date=end_date,
        class_id=filters.class_id,
        student_id=filters.student_id,
        subject_id=subject_id,
        top_n=top_n,
    )


@router.get(
    "/academic/export/csv",
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_academic_csv(
    filters: ReportFilter = Depends(report_filter_dependency),
    subject_id: int | None = None,
    top_n: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
) -> Response:
    data = _academic_data(db, filters, subject_id, top_n)
    csv_content = _write_csv(
        ["student_id", "student_code", "student_name", "class_name", "gpa", "percentage"],
        [
            [
                item["student_id"],
                item["student_code"],
                item["student_name"],
                item.get("class_name") or "",
                item["gpa"],
                item["percentage"],
            ]
            for item in data["top_students"]
        ],
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=academic_report_{date.today()}.csv"},
    )


@router.get(
    "/top-performers/export/csv",
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_top_performers_csv(
    filters: ReportFilter = Depends(report_filter_dependency),
    subject_id: int | None = None,
    top_n: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
) -> Response:
    data = _academic_data(db, filters, subject_id, top_n)
    csv_content = _write_csv(
        ["rank", "student_id", "student_code", "student_name", "class_name", "gpa", "percentage"],
        [
            [
                index,
                item["student_id"],
                item["student_code"],
                item["student_name"],
                item.get("class_name") or "",
                item["gpa"],
                item["percentage"],
            ]
            for index, item in enumerate(data["top_students"], start=1)
        ],
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=top_performers_report_{date.today()}.csv"},
    )


@router.get(
    "/students/export/csv",
    dependencies=[Depends(require_permission("reports.export"))],
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
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_attendance_csv(
    course_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    filters: ReportFilter = Depends(report_filter_dependency),
    detail: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Response:
    start_date, end_date = filters.effective_range()
    items, _ = report_service.get_attendance_report(
        db,
        course_id=course_id,
        class_id=filters.class_id,
        student_id=filters.student_id,
        status=status_filter,
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
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_fees_csv(
    course_id: int | None = None,
    category_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    due_from: date | None = None,
    due_to: date | None = None,
    filters: ReportFilter = Depends(report_filter_dependency),
    db: Session = Depends(get_db),
) -> Response:
    _validate_fee_category(db, category_id)
    period_start, period_end = filters.effective_range()
    effective_due_from = period_start or due_from
    effective_due_to = period_end or due_to
    _validate_date_range(effective_due_from, effective_due_to)
    items, _ = report_service.get_fee_report(
        db,
        student_id=filters.student_id,
        course_id=course_id,
        class_id=filters.class_id,
        category_id=category_id,
        status=report_status,
        due_from=effective_due_from,
        due_to=effective_due_to,
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
    dependencies=[Depends(require_permission("reports.export"))],
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
    "/academic/export/pdf",
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_academic_pdf(
    filters: ReportFilter = Depends(report_filter_dependency),
    subject_id: int | None = None,
    top_n: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
) -> Response:
    data = _academic_data(db, filters, subject_id, top_n)
    headers = ["Student ID", "Code", "Student", "Class", "GPA", "Percentage"]
    rows = [
        [
            str(item["student_id"]),
            item["student_code"],
            item["student_name"],
            item.get("class_name") or "",
            f"{item['gpa']:.2f}",
            f"{item['percentage']:.2f}",
        ]
        for item in data["top_students"]
    ]
    pdf_bytes = _build_pdf("Academic Performance Report", headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=academic_report_{date.today()}.pdf"},
    )


@router.get(
    "/top-performers/export/pdf",
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_top_performers_pdf(
    filters: ReportFilter = Depends(report_filter_dependency),
    subject_id: int | None = None,
    top_n: int = Query(default=10, ge=5, le=20),
    db: Session = Depends(get_db),
) -> Response:
    data = _academic_data(db, filters, subject_id, top_n)
    headers = ["Rank", "Student ID", "Code", "Student", "Class", "GPA", "Percentage"]
    rows = [
        [
            str(index),
            str(item["student_id"]),
            item["student_code"],
            item["student_name"],
            item.get("class_name") or "",
            f"{item['gpa']:.2f}",
            f"{item['percentage']:.2f}",
        ]
        for index, item in enumerate(data["top_students"], start=1)
    ]
    pdf_bytes = _build_pdf("Top Performers Report", headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=top_performers_report_{date.today()}.pdf"},
    )


@router.get(
    "/students/export/pdf",
    dependencies=[Depends(require_permission("reports.export"))],
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
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_attendance_pdf(
    course_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    filters: ReportFilter = Depends(report_filter_dependency),
    detail: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Response:
    start_date, end_date = filters.effective_range()
    items, _ = report_service.get_attendance_report(
        db,
        course_id=course_id,
        class_id=filters.class_id,
        student_id=filters.student_id,
        status=status_filter,
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
        headers = ["Student ID", "Code", "Name", "Course", "Total", "Present", "Absent", "Late", "Excused", "%"]
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
                str(item.excused_days),
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
    dependencies=[Depends(require_permission("reports.export"))],
)
def export_fees_pdf(
    course_id: int | None = None,
    category_id: int | None = None,
    report_status: str | None = Query(default=None, alias="status"),
    due_from: date | None = None,
    due_to: date | None = None,
    filters: ReportFilter = Depends(report_filter_dependency),
    db: Session = Depends(get_db),
) -> Response:
    _validate_fee_category(db, category_id)
    period_start, period_end = filters.effective_range()
    effective_due_from = period_start or due_from
    effective_due_to = period_end or due_to
    _validate_date_range(effective_due_from, effective_due_to)
    items, _ = report_service.get_fee_report(
        db,
        student_id=filters.student_id,
        course_id=course_id,
        class_id=filters.class_id,
        category_id=category_id,
        status=report_status,
        due_from=effective_due_from,
        due_to=effective_due_to,
        page=1,
        page_size=500,
    )
    headers = ["Student ID", "Code", "Name", "Course", "Title", "Category", "Total", "Paid", "Balance", "Due Date", "Status"]
    rows = [
        [
            str(item.student_id),
            item.student_code,
            item.student_name,
            item.course_name or "",
            item.title,
            item.fee_category or "",
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
    dependencies=[Depends(require_permission("reports.export"))],
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
