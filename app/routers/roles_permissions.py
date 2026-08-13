from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_permission
from app.models.role_permission import Role
from app.models.user import User
from app.schemas.role_permission import (
    PermissionResponse,
    RoleCreate,
    RoleListResponse,
    RolePermissionUpdate,
    RoleResponse,
    RoleUpdate,
)
from app.services import audit_service, role_permission_service


router = APIRouter(
    prefix="/roles-permissions",
    tags=["Roles & Permissions"],
)


def _get_role_or_404(db: Session, role_id: int) -> Role:
    role = role_permission_service.get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


def _build_role_response(db: Session, role: Role) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        is_system=role.is_system,
        is_active=role.is_active,
        user_count=role_permission_service.role_user_count(db, role),
        permission_codes=role_permission_service.permission_codes_for_role(role),
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.get("", response_model=RoleListResponse)
def get_roles_and_permissions(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("roles.view")),
) -> RoleListResponse:
    roles = role_permission_service.list_roles(db)
    permissions = role_permission_service.list_permissions(db)
    return RoleListResponse(
        roles=[_build_role_response(db, role) for role in roles],
        permissions=[PermissionResponse.model_validate(permission) for permission in permissions],
    )


@router.get("/roles", response_model=list[RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("roles.view")),
) -> list[RoleResponse]:
    return [_build_role_response(db, role) for role in role_permission_service.list_roles(db)]


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
) -> RoleResponse:
    try:
        role = role_permission_service.create_role(db, role_data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role could not be created") from error

    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="role_created",
        entity_type="role",
        entity_id=role.id,
        description=f"Role {role.display_name} created",
        metadata_json={"role": role.name, "permission_codes": role_permission_service.permission_codes_for_role(role)},
        ip_address=audit_service.get_request_ip(request),
    )
    return _build_role_response(db, role)


@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("roles.view")),
) -> RoleResponse:
    return _build_role_response(db, _get_role_or_404(db, role_id))


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
) -> RoleResponse:
    role = _get_role_or_404(db, role_id)
    old_name = role.name
    try:
        updated_role = role_permission_service.update_role(db, role, role_data)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role could not be updated") from error

    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="role_updated",
        entity_type="role",
        entity_id=updated_role.id,
        description=f"Role {updated_role.display_name} updated",
        metadata_json={"old_name": old_name, "new_name": updated_role.name},
        ip_address=audit_service.get_request_ip(request),
    )
    return _build_role_response(db, updated_role)


@router.patch("/roles/{role_id}/deactivate", response_model=RoleResponse)
def deactivate_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
) -> RoleResponse:
    role = _get_role_or_404(db, role_id)
    try:
        updated_role = role_permission_service.update_role(db, role, RoleUpdate(is_active=False))
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="role_deactivated",
        entity_type="role",
        entity_id=updated_role.id,
        description=f"Role {updated_role.display_name} deactivated",
        ip_address=audit_service.get_request_ip(request),
    )
    return _build_role_response(db, updated_role)


@router.patch("/roles/{role_id}/activate", response_model=RoleResponse)
def activate_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
) -> RoleResponse:
    role = _get_role_or_404(db, role_id)
    updated_role = role_permission_service.update_role(db, role, RoleUpdate(is_active=True))
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="role_updated",
        entity_type="role",
        entity_id=updated_role.id,
        description=f"Role {updated_role.display_name} activated",
        metadata_json={"is_active": True},
        ip_address=audit_service.get_request_ip(request),
    )
    return _build_role_response(db, updated_role)


@router.put("/roles/{role_id}/permissions", response_model=RoleResponse)
def update_role_permissions(
    role_id: int,
    permission_data: RolePermissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
) -> RoleResponse:
    role = _get_role_or_404(db, role_id)
    before = role_permission_service.permission_codes_for_role(role)
    try:
        updated_role = role_permission_service.set_role_permissions(db, role, permission_data)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    after = role_permission_service.permission_codes_for_role(updated_role)
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="role_permissions_changed",
        entity_type="role",
        entity_id=updated_role.id,
        description=f"Permissions changed for role {updated_role.display_name}",
        metadata_json={"before": before, "after": after},
        ip_address=audit_service.get_request_ip(request),
    )
    return _build_role_response(db, updated_role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
) -> None:
    role = _get_role_or_404(db, role_id)
    role_name = role.name
    try:
        role_permission_service.delete_role_if_unused(db, role)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    audit_service.record_audit_event(
        db,
        user_id=current_user.id,
        action="role_deleted",
        entity_type="role",
        description=f"Role {role_name} deleted",
        metadata_json={"role": role_name},
        ip_address=audit_service.get_request_ip(request),
    )
