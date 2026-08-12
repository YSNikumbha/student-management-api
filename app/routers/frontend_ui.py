from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_attendance_editor
from app.models.user import User
from app.services import frontend_service

router = APIRouter(
    prefix="/ui",
    tags=["Figma UI"],
)


class MarkAttendanceRecord(BaseModel):
    student_id: int
    status: str
    remarks: str | None = None


class MarkAttendanceRequest(BaseModel):
    class_id: int
    date: date
    records: list[MarkAttendanceRecord]


@router.get("/dashboard")
def get_dashboard_ui(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return frontend_service.get_dashboard_ui(db)


@router.get("/students")
def get_students_ui(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return frontend_service.get_students_ui(db)


@router.get("/classes")
def get_classes_ui(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return frontend_service.get_classes_ui(db)


@router.get("/attendance")
def get_attendance_ui(
    selected_date: date | None = None,
    class_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return frontend_service.get_attendance_ui(
        db,
        selected_date=selected_date or date.today(),
        class_id=class_id,
    )


@router.post("/attendance/mark")
def mark_attendance_ui(
    mark_data: MarkAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_attendance_editor),
) -> dict[str, int]:
    try:
        records = [record.model_dump() for record in mark_data.records]
        return frontend_service.mark_attendance_ui(
            db,
            class_id=mark_data.class_id,
            selected_date=mark_data.date,
            records=records,
            marked_by=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.get("/fees")
def get_fees_ui(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return frontend_service.get_fees_ui(db)


@router.get("/reports")
def get_reports_ui(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return frontend_service.get_reports_ui(db)
