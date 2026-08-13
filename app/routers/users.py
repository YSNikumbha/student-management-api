from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.schemas.user import PasswordResetRequest, UserCreate, UserResponse, UserUpdate
from app.services import audit_service, notification_service, role_permission_service, user_service


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def _ensure_unique_email(db: Session, email: str, user_id: int | None = None) -> None:
    existing_user = user_service.get_user_by_email(db, email)
    if existing_user is not None and existing_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )


def _build_user_response(db: Session, user: User) -> UserResponse:
    return user_service.build_user_response(db, user)


@router.get("", response_model=PaginatedResponse[UserResponse])
def get_users(
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("users.view")),
) -> dict[str, list[UserResponse] | int]:
    users, total_items = user_service.get_users_paginated(
        db,
        search=search,
        role=role,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return build_paginated_response([_build_user_response(db, user) for user in users], page, page_size, total_items)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.create")),
) -> UserResponse:
    _ensure_unique_email(db, str(user_data.email))

    try:
        user = user_service.create_user(db, user_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User could not be created",
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="user_created",
        entity_type="user",
        entity_id=user.id,
        description=f"User {user.email} created",
        metadata_json={"email": user.email, "role": user.role},
        ip_address=audit_service.get_request_ip(request),
    )
    notification_service.notify_account_created(db, user)
    return _build_user_response(db, user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("users.view")),
) -> UserResponse:
    return _build_user_response(db, _get_user_or_404(db, user_id))


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.edit")),
) -> UserResponse:
    user = _get_user_or_404(db, user_id)
    update_data = user_data.model_dump(exclude_unset=True)
    old_role = user.role
    old_is_active = user.is_active

    if user.id == current_user.id:
        if update_data.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You cannot deactivate your own account",
            )
        target_role_name = update_data.get("role")
        if update_data.get("role_id") is not None or target_role_name is not None:
            target_role = role_permission_service.get_role_by_identifier(
                db,
                role_id=update_data.get("role_id"),
                role_name=target_role_name,
            )
            if target_role is None or target_role.name not in {"admin", "super_admin"}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You cannot remove your own admin role",
                )
        if target_role_name is not None and target_role_name not in {"admin", "super_admin"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You cannot remove your own admin role",
            )

    if user_data.email is not None:
        _ensure_unique_email(db, str(user_data.email), user_id=user.id)

    try:
        updated_user = user_service.update_user(db, user, user_data)
    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User could not be updated",
        ) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="user_updated",
        entity_type="user",
        entity_id=updated_user.id,
        description=f"User {updated_user.email} updated",
        metadata_json={"updated_fields": sorted(update_data.keys())},
        ip_address=audit_service.get_request_ip(request),
    )
    if updated_user.role != old_role:
        audit_service.record_audit_event(
            db,
            user_id=current_user.id,
            action="role_changed",
            entity_type="user",
            entity_id=updated_user.id,
            description=f"User {updated_user.email} role changed",
            metadata_json={"old_role": old_role, "new_role": updated_user.role},
            ip_address=audit_service.get_request_ip(request),
        )
    if old_is_active and not updated_user.is_active:
        audit_service.record_audit_event(
            db,
            user_id=current_user.id,
            action="user_deactivated",
            entity_type="user",
            entity_id=updated_user.id,
            description=f"User {updated_user.email} deactivated",
            ip_address=audit_service.get_request_ip(request),
        )
    return _build_user_response(db, updated_user)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.deactivate")),
) -> UserResponse:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot deactivate your own account",
        )
    user = _get_user_or_404(db, user_id)
    updated_user = user_service.set_user_active(db, user, False)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="user_deactivated",
        entity_type="user",
        entity_id=updated_user.id,
        description=f"User {updated_user.email} deactivated",
        ip_address=audit_service.get_request_ip(request),
    )
    return _build_user_response(db, updated_user)


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.deactivate")),
) -> UserResponse:
    user = _get_user_or_404(db, user_id)
    updated_user = user_service.set_user_active(db, user, True)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="user_updated",
        entity_type="user",
        entity_id=updated_user.id,
        description=f"User {updated_user.email} activated",
        metadata_json={"is_active": True},
        ip_address=audit_service.get_request_ip(request),
    )
    return _build_user_response(db, updated_user)


@router.post("/{user_id}/reset-password", response_model=UserResponse)
def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.edit")),
) -> UserResponse:
    user = _get_user_or_404(db, user_id)
    updated_user = user_service.reset_user_password(db, user, password_data.new_password)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="user_password_reset",
        entity_type="user",
        entity_id=updated_user.id,
        description=f"User {updated_user.email} password reset",
        ip_address=audit_service.get_request_ip(request),
    )
    notification_service.notify_password_reset(db, updated_user)
    return _build_user_response(db, updated_user)
