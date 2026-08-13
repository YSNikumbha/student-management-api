from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_permission
from app.models.user import User
from app.schemas.dashboard import (
    CourseStatResponse,
    DashboardAttentionResponse,
    DashboardSummaryResponse,
    RecentActivityResponse,
)
from app.services import dashboard_service

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("dashboard.view")),
) -> DashboardSummaryResponse:
    return dashboard_service.get_dashboard_summary(db)


@router.get("/recent-activity", response_model=RecentActivityResponse)
def get_recent_activity(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("dashboard.view")),
) -> RecentActivityResponse:
    return dashboard_service.get_recent_activity(db)


@router.get("/course-stats", response_model=list[CourseStatResponse])
def get_course_stats(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("dashboard.view")),
) -> list[CourseStatResponse]:
    return dashboard_service.get_course_stats(db)


@router.get("/attention", response_model=DashboardAttentionResponse)
def get_dashboard_attention(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("dashboard.view")),
) -> DashboardAttentionResponse:
    return dashboard_service.get_dashboard_attention(db)
