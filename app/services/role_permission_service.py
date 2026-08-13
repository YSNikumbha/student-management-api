from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.role_permission import Permission, Role, RolePermission
from app.models.user import User
from app.schemas.role_permission import RoleCreate, RolePermissionUpdate, RoleUpdate


PermissionDef = tuple[str, str, str, str]


PERMISSION_DEFINITIONS: list[PermissionDef] = [
    ("dashboard.view", "View Dashboard", "View dashboard metrics and summaries", "Dashboard"),
    ("students.view", "View Students", "View student profiles and lists", "Students"),
    ("students.create", "Create Students", "Create student records", "Students"),
    ("students.edit", "Edit Students", "Update student records", "Students"),
    ("students.delete", "Delete Students", "Delete student records", "Students"),
    ("classes.view", "View Classes", "View classes and batches", "Classes"),
    ("classes.create", "Create Classes", "Create classes and batches", "Classes"),
    ("classes.edit", "Edit Classes", "Update classes and batches", "Classes"),
    ("classes.delete", "Delete Classes", "Delete classes and batches", "Classes"),
    ("attendance.view", "View Attendance", "View attendance records and sessions", "Attendance"),
    ("attendance.mark", "Mark Attendance", "Mark student attendance", "Attendance"),
    ("attendance.edit", "Edit Attendance", "Update attendance records", "Attendance"),
    ("attendance.delete", "Delete Attendance", "Delete attendance records", "Attendance"),
    ("fees.view", "View Fees", "View fee records and payments", "Fee Management"),
    ("fees.create", "Create Fees", "Create fee records and structures", "Fee Management"),
    ("fees.edit", "Edit Fees", "Update fee records and structures", "Fee Management"),
    ("fees.delete", "Delete Fees", "Delete fee records and structures", "Fee Management"),
    ("fees.record_payment", "Record Payments", "Record student fee payments", "Fee Management"),
    ("reports.view", "View Reports", "View academic, attendance, and finance reports", "Reports"),
    ("reports.export", "Export Reports", "Export reports as CSV or PDF", "Reports"),
    ("users.view", "View Users", "View user accounts", "User Management"),
    ("users.create", "Create Users", "Create user accounts", "User Management"),
    ("users.edit", "Edit Users", "Update user accounts", "User Management"),
    ("users.deactivate", "Deactivate Users", "Deactivate user accounts", "User Management"),
    ("roles.view", "View Roles", "View roles and permissions", "Roles & Permissions"),
    ("roles.manage", "Manage Roles", "Create roles and change permissions", "Roles & Permissions"),
    ("settings.view", "View Settings", "View system settings", "Settings"),
    ("settings.edit", "Edit Settings", "Update system settings", "Settings"),
    ("notifications.view", "View Notifications", "View notifications", "Notifications"),
    ("notifications.manage", "Manage Notifications", "Manage notification preferences and messages", "Notifications"),
    ("audit.view", "View Audit Logs", "View audit logs", "Audit"),
]

ALL_PERMISSION_CODES = [code for code, _name, _description, _module in PERMISSION_DEFINITIONS]
VIEW_PERMISSION_CODES = [code for code in ALL_PERMISSION_CODES if code.endswith(".view")]
OPERATIONAL_PERMISSION_CODES = [
    code
    for code in ALL_PERMISSION_CODES
    if code
    not in {
        "roles.manage",
        "students.delete",
        "classes.delete",
        "attendance.delete",
        "fees.delete",
    }
]

ROLE_DEFINITIONS: dict[str, dict[str, object]] = {
    "super_admin": {
        "display_name": "Super Admin",
        "description": "Full system access including protected system roles.",
        "permissions": ALL_PERMISSION_CODES,
    },
    "admin": {
        "display_name": "Admin",
        "description": "Operational administrator with users, reports, and settings access.",
        "permissions": ALL_PERMISSION_CODES,
    },
    "teacher": {
        "display_name": "Teacher",
        "description": "Academic staff access for students, classes, attendance, and academic reports.",
        "permissions": [
            "dashboard.view",
            "students.view",
            "classes.view",
            "attendance.view",
            "attendance.mark",
            "attendance.edit",
            "reports.view",
        ],
    },
    "accountant": {
        "display_name": "Accountant",
        "description": "Finance staff access for fees, payments, and financial reporting.",
        "permissions": [
            "dashboard.view",
            "students.view",
            "classes.view",
            "fees.view",
            "fees.create",
            "fees.edit",
            "fees.record_payment",
            "reports.view",
            "reports.export",
        ],
    },
    "staff": {
        "display_name": "Staff",
        "description": "Legacy staff role preserved for existing installations.",
        "permissions": [
            "dashboard.view",
            "students.view",
            "classes.view",
            "attendance.view",
            "attendance.mark",
            "attendance.edit",
            "fees.view",
            "fees.record_payment",
            "reports.view",
            "reports.export",
            "settings.view",
            "notifications.view",
        ],
    },
    "viewer": {
        "display_name": "Viewer",
        "description": "Read-only access to operational modules.",
        "permissions": VIEW_PERMISSION_CODES,
    },
}

ROLE_ALIASES = {
    "superadmin": "super_admin",
    "super_admin": "super_admin",
    "super admin": "super_admin",
    "admin": "admin",
    "administrator": "admin",
    "teacher": "teacher",
    "accountant": "accountant",
    "staff": "staff",
    "viewer": "viewer",
}

PROTECTED_SYSTEM_ROLE_NAMES = {"super_admin"}


def normalize_role_name(value: str) -> str:
    cleaned = value.strip().lower().replace("-", "_")
    alias_key = cleaned.replace("_", " ")
    return ROLE_ALIASES.get(cleaned, ROLE_ALIASES.get(alias_key, cleaned))


def default_permissions_for_role(role_name: str) -> set[str]:
    role = ROLE_DEFINITIONS.get(normalize_role_name(role_name))
    if not role:
        return set()
    return set(role["permissions"])  # type: ignore[arg-type]


def ensure_default_roles_and_permissions(db: Session) -> None:
    permission_by_code: dict[str, Permission] = {
        permission.code: permission
        for permission in db.execute(select(Permission)).scalars().all()
    }
    changed = False
    for code, name, description, module in PERMISSION_DEFINITIONS:
        permission = permission_by_code.get(code)
        if permission is None:
            permission = Permission(
                code=code,
                name=name,
                description=description,
                module=module,
            )
            db.add(permission)
            permission_by_code[code] = permission
            changed = True
        else:
            permission.name = name
            permission.description = description
            permission.module = module

    role_by_name: dict[str, Role] = {
        role.name: role
        for role in db.execute(
            select(Role).options(selectinload(Role.role_permissions))
        ).scalars().all()
    }
    for name, definition in ROLE_DEFINITIONS.items():
        role = role_by_name.get(name)
        if role is None:
            role = Role(
                name=name,
                display_name=str(definition["display_name"]),
                description=str(definition["description"]),
                is_system=True,
                is_active=True,
            )
            db.add(role)
            role_by_name[name] = role
            changed = True
        else:
            role.display_name = str(definition["display_name"])
            role.description = str(definition["description"])
            role.is_system = True
            role.is_active = True

    if changed:
        db.flush()

    permissions = {
        permission.code: permission
        for permission in db.execute(select(Permission)).scalars().all()
    }
    roles = {
        role.name: role
        for role in db.execute(
            select(Role).options(selectinload(Role.role_permissions))
        ).scalars().all()
    }
    for name, definition in ROLE_DEFINITIONS.items():
        role = roles[name]
        existing_permission_ids = {role_permission.permission_id for role_permission in role.role_permissions}
        for code in definition["permissions"]:  # type: ignore[union-attr]
            permission = permissions[str(code)]
            if permission.id not in existing_permission_ids:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

    for user in db.execute(select(User).where(User.role_id.is_(None))).scalars().all():
        role_name = normalize_role_name(user.role)
        role = roles.get(role_name)
        if role is not None:
            user.role = role.name
            user.role_id = role.id

    db.commit()


def list_permissions(db: Session) -> list[Permission]:
    ensure_default_roles_and_permissions(db)
    return list(db.execute(select(Permission).order_by(Permission.module, Permission.code)).scalars().all())


def list_roles(db: Session) -> list[Role]:
    ensure_default_roles_and_permissions(db)
    return list(
        db.execute(
            select(Role)
            .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
            .order_by(Role.is_system.desc(), Role.display_name)
        ).scalars().all()
    )


def get_role(db: Session, role_id: int) -> Role | None:
    ensure_default_roles_and_permissions(db)
    return db.execute(
        select(Role)
        .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        .where(Role.id == role_id)
    ).scalar_one_or_none()


def get_role_by_name(db: Session, role_name: str) -> Role | None:
    ensure_default_roles_and_permissions(db)
    normalized = normalize_role_name(role_name)
    return db.execute(
        select(Role)
        .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        .where(Role.name == normalized)
    ).scalar_one_or_none()


def get_role_by_identifier(db: Session, *, role_id: int | None = None, role_name: str | None = None) -> Role | None:
    if role_id is not None:
        return get_role(db, role_id)
    if role_name:
        return get_role_by_name(db, role_name)
    return get_role_by_name(db, "teacher")


def permission_codes_for_role(role: Role) -> list[str]:
    return sorted(
        role_permission.permission.code
        for role_permission in role.role_permissions
        if role_permission.permission is not None
    )


def role_user_count(db: Session, role: Role) -> int:
    return db.execute(select(func.count(User.id)).where(User.role_id == role.id)).scalar_one()


def create_role(db: Session, data: RoleCreate) -> Role:
    ensure_default_roles_and_permissions(db)
    if get_role_by_name(db, data.name) is not None:
        raise ValueError("A role with this name already exists")
    role = Role(
        name=normalize_role_name(data.name),
        display_name=data.display_name,
        description=data.description,
        is_system=False,
        is_active=data.is_active,
    )
    db.add(role)
    db.flush()
    set_role_permissions(
        db,
        role,
        RolePermissionUpdate(permission_codes=data.permission_codes),
        commit=False,
        ensure_defaults=False,
    )
    db.commit()
    db.refresh(role)
    return get_role(db, role.id) or role


def update_role(db: Session, role: Role, data: RoleUpdate) -> Role:
    update_data = data.model_dump(exclude_unset=True)
    if role.name in PROTECTED_SYSTEM_ROLE_NAMES and any(field in update_data for field in ("name", "is_active")):
        raise ValueError("This system role cannot be renamed or deactivated")
    if role.is_system and "name" in update_data and update_data["name"] != role.name:
        raise ValueError("System roles cannot be renamed")
    if "name" in update_data and update_data["name"] is not None:
        normalized = normalize_role_name(update_data["name"])
        existing = get_role_by_name(db, normalized)
        if existing is not None and existing.id != role.id:
            raise ValueError("A role with this name already exists")
        old_name = role.name
        role.name = normalized
        for user in db.execute(select(User).where(User.role == old_name)).scalars().all():
            user.role = normalized
    if "display_name" in update_data and update_data["display_name"] is not None:
        role.display_name = update_data["display_name"]
    if "description" in update_data:
        role.description = update_data["description"]
    if "is_active" in update_data and update_data["is_active"] is not None:
        role.is_active = update_data["is_active"]
    role.updated_at = datetime.now(UTC)
    db.add(role)
    db.commit()
    db.refresh(role)
    return get_role(db, role.id) or role


def set_role_permissions(
    db: Session,
    role: Role,
    data: RolePermissionUpdate,
    *,
    commit: bool = True,
    ensure_defaults: bool = True,
) -> Role:
    if ensure_defaults:
        ensure_default_roles_and_permissions(db)
    if role.name in PROTECTED_SYSTEM_ROLE_NAMES:
        target_codes = set(ALL_PERMISSION_CODES)
    else:
        target_codes = set(data.permission_codes)
    permissions = {
        permission.code: permission
        for permission in db.execute(select(Permission).where(Permission.code.in_(target_codes))).scalars().all()
    }
    missing_codes = sorted(target_codes - set(permissions))
    if missing_codes:
        raise ValueError(f"Unknown permission codes: {', '.join(missing_codes)}")
    existing = {
        role_permission.permission_id: role_permission
        for role_permission in db.execute(
            select(RolePermission).where(RolePermission.role_id == role.id)
        ).scalars().all()
    }
    target_ids = {permission.id for permission in permissions.values()}
    for permission in permissions.values():
        if permission.id not in existing:
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    for permission_id, role_permission in existing.items():
        if permission_id not in target_ids:
            db.delete(role_permission)
    role.updated_at = datetime.now(UTC)
    if commit:
        db.commit()
    else:
        db.flush()
    return get_role(db, role.id) or role


def delete_role_if_unused(db: Session, role: Role) -> None:
    if role.is_system:
        raise ValueError("System roles cannot be deleted")
    if role_user_count(db, role) > 0:
        raise ValueError("Role cannot be deleted while assigned to users")
    db.delete(role)
    db.commit()


def permissions_for_user(db: Session, user: User) -> set[str]:
    ensure_default_roles_and_permissions(db)
    if user.role_id is not None:
        role = get_role(db, user.role_id)
        if role is not None and role.is_active:
            return set(permission_codes_for_role(role))
    role_name = normalize_role_name(user.role)
    role = get_role_by_name(db, role_name)
    if role is not None and role.is_active:
        return set(permission_codes_for_role(role))
    return default_permissions_for_role(role_name)


def user_has_permission(db: Session, user: User, permission_code: str) -> bool:
    if normalize_role_name(user.role) in {"admin", "super_admin"}:
        return True
    return permission_code in permissions_for_user(db, user)


def assign_role_to_user(db: Session, user: User, *, role_id: int | None = None, role_name: str | None = None) -> Role:
    role = get_role_by_identifier(db, role_id=role_id, role_name=role_name)
    if role is None or not role.is_active:
        raise ValueError("Role not found or inactive")
    user.role_id = role.id
    user.role = role.name
    db.add(user)
    return role
