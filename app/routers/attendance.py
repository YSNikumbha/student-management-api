from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceBulkResponse,
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    CourseAttendanceResponse,
    CourseAttendanceStudent,
    StudentAttendanceSummary,
)
from app.services import attendance_service, course_service, student_service


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


def _get_student_or_404(db: Session, student_id: int) -> None:
    if student_service.get_student_by_id(db, student_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )


def _get_course_or_404(db: Session, course_id: int) -> None:
    if course_service.get_course_by_id(db, course_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )


@router.post(
    "",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Attendance:
    _get_student_or_404(db, attendance_data.student_id)

    existing_attendance = attendance_service.get_attendance_for_student_date(
        db,
        attendance_data.student_id,
        attendance_data.date,
    )
    if existing_attendance is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this student on this date",
        )

    try:
        return attendance_service.create_attendance(
            db,
            attendance_data,
            marked_by=current_user.id,
        )
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this student on this date",
        ) from error


@router.post("/bulk", response_model=AttendanceBulkResponse)
def bulk_mark_attendance(
    attendance_data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceBulkResponse:
    student_ids = [record.student_id for record in attendance_data.records]
    unique_student_ids = set(student_ids)

    if len(unique_student_ids) != len(student_ids):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate student in attendance request",
        )

    existing_student_ids = attendance_service.get_existing_student_ids(
        db,
        unique_student_ids,
    )
    if existing_student_ids != unique_student_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    try:
        created, updated, records = attendance_service.bulk_upsert_attendance(
            db,
            attendance_data.date,
            attendance_data.records,
            marked_by=current_user.id,
        )
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this student on this date",
        ) from error

    return AttendanceBulkResponse(
        date=attendance_data.date,
        created=created,
        updated=updated,
        records=records,
    )


@router.get("", response_model=list[AttendanceResponse])
def get_attendance_records(
    attendance_date: date | None = Query(default=None, alias="date"),
    student_id: int | None = None,
    course_id: int | None = None,
    attendance_status: AttendanceStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Attendance]:
    if student_id is not None:
        _get_student_or_404(db, student_id)

    if course_id is not None:
        _get_course_or_404(db, course_id)

    return attendance_service.get_attendance_records(
        db,
        attendance_date=attendance_date,
        student_id=student_id,
        course_id=course_id,
        status=attendance_status.value if attendance_status else None,
    )


@router.get(
    "/student/{student_id}/summary",
    response_model=StudentAttendanceSummary,
)
def get_student_attendance_summary(
    student_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> StudentAttendanceSummary:
    _get_student_or_404(db, student_id)
    summary = attendance_service.calculate_student_attendance_summary(db, student_id)
    return StudentAttendanceSummary(**summary)


@router.get("/student/{student_id}", response_model=list[AttendanceResponse])
def get_student_attendance(
    student_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Attendance]:
    _get_student_or_404(db, student_id)
    return attendance_service.get_student_attendance(
        db,
        student_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/date/{attendance_date}", response_model=list[AttendanceResponse])
def get_attendance_by_date(
    attendance_date: date,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Attendance]:
    return attendance_service.get_attendance_by_date(db, attendance_date)


@router.get(
    "/course/{course_id}/date/{attendance_date}",
    response_model=CourseAttendanceResponse,
)
def get_course_attendance_by_date(
    course_id: int,
    attendance_date: date,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CourseAttendanceResponse:
    _get_course_or_404(db, course_id)
    course_attendance = attendance_service.get_course_attendance_by_date(
        db,
        course_id,
        attendance_date,
    )
    students = [
        CourseAttendanceStudent(
            student_id=student.id,
            student_code=student.student_code,
            name=f"{student.first_name} {student.last_name}",
            attendance_id=attendance.id if attendance else None,
            status=attendance.status if attendance else None,
            remarks=attendance.remarks if attendance else None,
        )
        for student, attendance in course_attendance
    ]

    return CourseAttendanceResponse(
        course_id=course_id,
        date=attendance_date,
        students=students,
    )


@router.get("/{attendance_id}", response_model=AttendanceResponse)
def get_attendance_by_id(
    attendance_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Attendance:
    attendance = attendance_service.get_attendance_by_id(db, attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )

    return attendance


@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    attendance_id: int,
    attendance_data: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Attendance:
    attendance = attendance_service.get_attendance_by_id(db, attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )

    return attendance_service.update_attendance(
        db,
        attendance,
        attendance_data,
        marked_by=current_user.id,
    )


@router.delete(
    "/{attendance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
) -> Response:
    attendance = attendance_service.get_attendance_by_id(db, attendance_id)
    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )

    attendance_service.delete_attendance(db, attendance)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
