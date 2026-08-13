from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import role_permission_service


def get_user_by_id(db: Session, user_id: int) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.execute(statement).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    statement = select(User).where(func.lower(User.email) == normalized_email)
    return db.execute(statement).scalar_one_or_none()


def build_user_response(db: Session, user: User) -> UserResponse:
    role = role_permission_service.get_role(db, user.role_id) if user.role_id else None
    permissions = sorted(role_permission_service.permissions_for_user(db, user))
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        role_id=user.role_id,
        role_display_name=role.display_name if role else user.role.replace("_", " ").title(),
        permissions=permissions,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def get_users_paginated(
    db: Session,
    *,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[User], int]:
    filters = []

    if search:
        search_value = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(User.name).like(search_value),
                func.lower(User.email).like(search_value),
            )
        )

    if role:
        filters.append(User.role == role)

    if is_active is not None:
        filters.append(User.is_active == is_active)

    total_statement = select(func.count(User.id)).where(*filters)
    total_items = db.execute(total_statement).scalar_one()

    offset = (page - 1) * page_size
    statement = (
        select(User)
        .where(*filters)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = list(db.execute(statement).scalars().all())
    return users, total_items


def _role_value(role: object) -> str:
    return str(getattr(role, "value", role)).strip().lower().replace(" ", "_").replace("-", "_")


def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(
        name=user_data.name.strip(),
        email=str(user_data.email).lower(),
        hashed_password=hash_password(user_data.password),
        role=_role_value(user_data.role),
        is_active=user_data.is_active,
    )
    role_permission_service.assign_role_to_user(
        db,
        user,
        role_id=user_data.role_id,
        role_name=_role_value(user_data.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    update_data = user_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        user.name = update_data["name"].strip()
    if "email" in update_data and update_data["email"] is not None:
        user.email = str(update_data["email"]).lower()
    if (
        ("role_id" in update_data and update_data["role_id"] is not None)
        or ("role" in update_data and update_data["role"] is not None)
    ):
        role_permission_service.assign_role_to_user(
            db,
            user,
            role_id=update_data.get("role_id"),
            role_name=_role_value(update_data["role"]) if update_data.get("role") else None,
        )
    if "is_active" in update_data and update_data["is_active"] is not None:
        user.is_active = update_data["is_active"]

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_user_active(db: Session, user: User, is_active: bool) -> User:
    user.is_active = is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user: User, new_password: str) -> User:
    user.hashed_password = hash_password(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def record_last_login(db: Session, user: User) -> User:
    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
