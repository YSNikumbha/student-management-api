from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.schemas.pagination import PaginatedResponse, build_paginated_response
from app.services import audit_service


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
def get_audit_logs(
    user_id: int | None = Query(default=None, alias="user"),
    action: str | None = None,
    entity_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> dict:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date must be before end_date",
        )

    logs, total_items = audit_service.get_audit_logs_paginated(
        db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        page_size=page_size,
    )
    responses = [audit_service.build_audit_log_response(log) for log in logs]
    return build_paginated_response(responses, page, page_size, total_items)
