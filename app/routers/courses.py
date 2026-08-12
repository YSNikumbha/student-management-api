from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.services import audit_service, course_service


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


def _duplicate_detail(_error: IntegrityError) -> str:
    return "A course with this code already exists"


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course_data: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Course:
    if course_service.get_course_by_code(db, course_data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this code already exists",
        )

    try:
        course = course_service.create_course(db, course_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="course_created",
        entity_type="course",
        entity_id=course.id,
        description=f"Course {course.code} created",
        metadata_json={"code": course.code, "name": course.name},
        ip_address=audit_service.get_request_ip(request),
    )
    return course


@router.get(
    "",
    response_model=PaginatedResponse[CourseResponse],
    dependencies=[Depends(get_current_user)],
)
def get_courses(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: Literal["name", "code", "created_at"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
) -> dict[str, list[Course] | int]:
    courses, total_items = course_service.get_courses_paginated(
        db,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return build_paginated_response(courses, page, page_size, total_items)


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(get_current_user)],
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
) -> Course:
    course = course_service.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return course


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)],
)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Course:
    course = course_service.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    update_data = course_data.model_dump(exclude_unset=True)
    code = update_data.get("code")
    if code is not None and code != course.code:
        existing_course = course_service.get_course_by_code(db, code)
        if existing_course is not None and existing_course.id != course.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A course with this code already exists",
            )

    try:
        updated_course = course_service.update_course(db, course, course_data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_duplicate_detail(error),
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="course_updated",
        entity_type="course",
        entity_id=updated_course.id,
        description=f"Course {updated_course.code} updated",
        metadata_json={"updated_fields": sorted(update_data.keys())},
        ip_address=audit_service.get_request_ip(request),
    )
    return updated_course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
) -> Response:
    course = course_service.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if course_service.course_has_students(db, course_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete course because students are assigned to it",
        )

    course_service.delete_course(db, course)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
