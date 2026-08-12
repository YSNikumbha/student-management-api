from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.system_setting import NotificationPreference, SystemSetting
from app.models.user import User
from app.schemas.settings import NotificationPreferenceUpdate, SystemSettingUpdate


def get_or_create_system_settings(db: Session) -> SystemSetting:
    settings = db.execute(select(SystemSetting).order_by(SystemSetting.id.asc())).scalar_one_or_none()
    if settings is not None:
        return settings
    settings = SystemSetting()
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_system_settings(db: Session, data: SystemSettingUpdate) -> SystemSetting:
    settings = get_or_create_system_settings(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    settings.updated_at = datetime.now(UTC)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def get_or_create_notification_preferences(
    db: Session,
    *,
    user_id: int,
) -> NotificationPreference:
    prefs = db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    ).scalar_one_or_none()
    if prefs is not None:
        return prefs
    prefs = NotificationPreference(user_id=user_id)
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


def update_notification_preferences(
    db: Session,
    *,
    user_id: int,
    data: NotificationPreferenceUpdate,
) -> NotificationPreference:
    prefs = get_or_create_notification_preferences(db, user_id=user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    prefs.updated_at = datetime.now(UTC)
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


def change_user_password(
    db: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> bool:
    if not verify_password(current_password, user.hashed_password):
        return False
    user.hashed_password = hash_password(new_password)
    db.add(user)
    db.commit()
    return True
