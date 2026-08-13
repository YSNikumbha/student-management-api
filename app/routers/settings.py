from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_permission
from app.models.user import User
from app.schemas.settings import (
    ChangePasswordRequest,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    SystemSettingResponse,
    SystemSettingUpdate,
)
from app.services import settings_service

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


@router.get("/system", response_model=SystemSettingResponse)
def get_system_settings(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("settings.view")),
):
    return settings_service.get_or_create_system_settings(db)


@router.put("/system", response_model=SystemSettingResponse)
def update_system_settings(
    settings_data: SystemSettingUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("settings.edit")),
):
    return settings_service.update_system_settings(db, settings_data)


@router.get("/notification-preferences", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return settings_service.get_or_create_notification_preferences(db, user_id=current_user.id)


@router.put("/notification-preferences", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    preference_data: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return settings_service.update_notification_preferences(
        db,
        user_id=current_user.id,
        data=preference_data,
    )


@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    changed = settings_service.change_user_password(
        db,
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )
    if not changed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    return {"message": "Password changed successfully"}
