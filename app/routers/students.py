from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_permission
from app.models.student import Student
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.services import audit_service, course_service, fee_service, student_service


router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


def _duplicate_detail(error: IntegrityError) -> str:
    error_text = str(error.orig)
    if "students.email" in error_text:
        return "A student with this email already exists"
    if "students.student_code" in error_text:
        return "A student with this student code already exists"
    return "A student with this email or student code already exists"


def _validate_course_id(db: Session, course_id: int | None) -> None:
    if course_id is not None and course_service.get_course_by_id(db, course_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    student_data: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("students.create")),
) -> Student:
    _validate_course_id(db, student_data.course_id)

    if student_service.get_student_by_email(db, student_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email already exists",
        )

    if student_service.get_student_by_code(db, student_data.student_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this student code already exists",
        )

    try:
        student = student_service.create_student(db, student_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="student_created",
        entity_type="student",
        entity_id=student.id,
        description=f"Student {student.student_code} created",
        metadata_json={"student_code": student.student_code, "email": student.email},
        ip_address=audit_service.get_request_ip(request),
    )
    return student


@router.get(
    "",
    response_model=PaginatedResponse[StudentResponse],
    dependencies=[Depends(require_permission("students.view"))],
)
def get_students(
    search: str | None = None,
    course_id: int | None = None,
    student_status: Literal["active", "inactive"] | None = Query(
        default=None,
        alias="status",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: Literal["created_at", "first_name", "last_name", "student_code"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
) -> dict[str, list[Student] | int]:
    students, total_items = student_service.get_students_paginated(
        db,
        search=search,
        course_id=course_id,
        status=student_status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return build_paginated_response(students, page, page_size, total_items)


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission("students.view"))],
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
) -> Student:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission("students.edit"))],
)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("students.edit")),
) -> Student:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    update_data = student_data.model_dump(exclude_unset=True)
    if "course_id" in update_data:
        _validate_course_id(db, update_data["course_id"])
    old_status = student.status

    email = update_data.get("email")
    if email is not None and email != student.email:
        existing_student = student_service.get_student_by_email(db, email)
        if existing_student is not None and existing_student.id != student.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this email already exists",
            )

    student_code = update_data.get("student_code")
    if student_code is not None and student_code != student.student_code:
        existing_student = student_service.get_student_by_code(db, student_code)
        if existing_student is not None and existing_student.id != student.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this student code already exists",
            )

    try:
        updated_student = student_service.update_student(db, student, student_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="student_updated",
        entity_type="student",
        entity_id=updated_student.id,
        description=f"Student {updated_student.student_code} updated",
        metadata_json={"updated_fields": sorted(update_data.keys())},
        ip_address=audit_service.get_request_ip(request),
    )
    if "status" in update_data and updated_student.status != old_status:
        audit_service.record_audit_event(
            db,
            user_id=current_user.id,
            action="student_status_changed",
            entity_type="student",
            entity_id=updated_student.id,
            description=f"Student {updated_student.student_code} status changed",
            metadata_json={"old_status": old_status, "new_status": updated_student.status},
            ip_address=audit_service.get_request_ip(request),
        )
    return updated_student


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("students.delete"))],
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
) -> Response:
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    if fee_service.student_has_fees(db, student.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete student because fee records exist",
        )

    try:
        student_service.delete_student(db, student)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete student because related records exist",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
