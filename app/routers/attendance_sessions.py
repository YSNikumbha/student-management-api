from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.attendance_session import AttendanceSession
from app.models.user import User
from app.schemas.attendance_session import (
    AttendanceBulkCreate,
    AttendanceSessionCreate,
    AttendanceSessionResponse,
    AttendanceSessionUpdate,
    AttendanceSessionWithDetails,
)
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.services import attendance_session_service

router = APIRouter(prefix="/attendance", tags=["Attendance Sessions"])


@router.post(
    "/sessions",
    response_model=AttendanceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    session_data: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AttendanceSession:
    try:
        return attendance_session_service.create_attendance_session(
            db, session_data, created_by=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/sessions",
    response_model=PaginatedResponse[AttendanceSessionWithDetails],
    dependencies=[Depends(get_current_user)],
)
def get_sessions(
    course_id: int | None = None,
    batch_id: int | None = None,
    semester_id: int | None = None,
    subject_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    skip = (page - 1) * page_size
    sessions, total = attendance_session_service.get_attendance_sessions(
        db,
        course_id=course_id,
        batch_id=batch_id,
        semester_id=semester_id,
        subject_id=subject_id,
        skip=skip,
        limit=page_size,
    )

    detailed_sessions = []
    for session in sessions:
        session_dict = {
            "id": session.id,
            "date": session.date,
            "course_id": session.course_id,
            "batch_id": session.batch_id,
            "semester_id": session.semester_id,
            "subject_id": session.subject_id,
            "session_name": session.session_name,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "created_by": session.created_by,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "course_name": session.course.name if session.course else None,
            "batch_name": session.batch.name if session.batch else None,
            "semester_name": session.semester.name if session.semester else None,
            "subject_name": session.subject.name if session.subject else None,
            "subject_code": session.subject.code if session.subject else None,
            "created_by_name": session.created_by_user.name if session.created_by_user else None,
            "student_count": len(session.attendance_records),
        }
        detailed_sessions.append(AttendanceSessionWithDetails(**session_dict))

    return build_paginated_response(detailed_sessions, page, page_size, total)


@router.get(
    "/sessions/{session_id}",
    response_model=AttendanceSessionWithDetails,
    dependencies=[Depends(get_current_user)],
)
def get_session(session_id: int, db: Session = Depends(get_db)) -> AttendanceSession:
    session = attendance_session_service.get_attendance_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found",
        )

    return AttendanceSessionWithDetails(
        id=session.id,
        date=session.date,
        course_id=session.course_id,
        batch_id=session.batch_id,
        semester_id=session.semester_id,
        subject_id=session.subject_id,
        session_name=session.session_name,
        start_time=session.start_time,
        end_time=session.end_time,
        created_by=session.created_by,
        created_at=session.created_at,
        updated_at=session.updated_at,
        course_name=session.course.name if session.course else None,
        batch_name=session.batch.name if session.batch else None,
        semester_name=session.semester.name if session.semester else None,
        subject_name=session.subject.name if session.subject else None,
        subject_code=session.subject.code if session.subject else None,
        created_by_name=session.created_by_user.name if session.created_by_user else None,
        student_count=len(session.attendance_records),
    )


@router.put(
    "/sessions/{session_id}",
    response_model=AttendanceSessionResponse,
)
def update_session(
    session_id: int,
    session_data: AttendanceSessionUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> AttendanceSession:
    session = attendance_session_service.update_attendance_session(db, session_id, session_data)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found",
        )
    return session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> Response:
    if not attendance_session_service.delete_attendance_session(db, session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/sessions/{session_id}/students",
    dependencies=[Depends(get_current_user)],
)
def get_session_students(session_id: int, db: Session = Depends(get_db)) -> dict:
    students = attendance_session_service.get_session_students(db, session_id)
    return {"students": students}


@router.post(
    "/sessions/{session_id}/records/bulk",
    status_code=status.HTTP_201_CREATED,
)
def bulk_create_records(
    session_id: int,
    records: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    try:
        result = attendance_session_service.bulk_create_attendance(
            db,
            session_id,
            [record.model_dump() for record in records.records],
            marked_by=current_user.id,
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found",
        )
    return {
        "message": "Attendance records saved successfully",
        **result,
    }


@router.get(
    "/sessions/student/{student_id}/summary",
    dependencies=[Depends(get_current_user)],
)
def get_student_summary(student_id: int, db: Session = Depends(get_db)) -> dict:
    summary = attendance_session_service.get_student_attendance_summary(db, student_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return summary


@router.get(
    "/sessions/student/{student_id}/subject-summary",
    dependencies=[Depends(get_current_user)],
)
def get_student_subject_summary(student_id: int, db: Session = Depends(get_db)) -> dict:
    summaries = attendance_session_service.get_student_subject_summary(db, student_id)
    return {"student_id": student_id, "subjects": summaries}
