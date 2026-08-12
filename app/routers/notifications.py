from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationUnreadCountResponse
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.services import notification_service

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def get_notifications(
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    notification_service.generate_user_notifications(db, current_user)
    notifications, total_items = notification_service.get_notifications_paginated(
        db,
        user_id=current_user.id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    return build_paginated_response(notifications, page, page_size, total_items)


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCountResponse:
    notification_service.generate_user_notifications(db, current_user)
    return NotificationUnreadCountResponse(
        unread_count=notification_service.get_unread_count(db, user_id=current_user.id),
    )


@router.put("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    updated = notification_service.mark_all_read(db, user_id=current_user.id)
    return {"updated": updated}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    notification = notification_service.get_user_notification(
        db,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return notification_service.mark_notification_read(db, notification)
