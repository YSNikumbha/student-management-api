from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.database import get_db
from app.routers.academic_performance import router as academic_performance_router
from app.routers.academic_years import router as academic_years_router
from app.routers.attendance import router as attendance_router
from app.routers.attendance_sessions import router as attendance_sessions_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.auth import router as auth_router
from app.routers.batches import router as batches_router
from app.routers.classes import router as classes_router
from app.routers.courses import router as courses_router
from app.routers.dashboard import router as dashboard_router
from app.routers.fees import router as fees_router
from app.routers.frontend_ui import router as frontend_ui_router
from app.routers.notifications import router as notifications_router
from app.routers.payments import router as payments_router
from app.routers.reports import router as reports_router
from app.routers.roles_permissions import router as roles_permissions_router
from app.routers.search import router as search_router
from app.routers.semesters import router as semesters_router
from app.routers.settings import router as settings_router
from app.routers.student_documents import router as student_documents_router
from app.routers.students import router as students_router
from app.routers.subjects import router as subjects_router
from app.routers.users import router as users_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
FRONTEND_INDEX = FRONTEND_DIST_DIR / "index.html"

app = FastAPI(
    title="Student Management API",
    description="Backend API for managing students, courses, attendance, and fees.",
    version="1.0.0",
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Content-Disposition"],
    )


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/health/live")
def read_liveness() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/health/ready")
def read_readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        ) from error

    return {"status": "ready"}

app.include_router(auth_router)
app.include_router(academic_performance_router)
app.include_router(academic_years_router)
app.include_router(semesters_router)
app.include_router(subjects_router)
app.include_router(batches_router)
app.include_router(classes_router)
app.include_router(student_documents_router)
app.include_router(students_router)
app.include_router(courses_router)
app.include_router(attendance_sessions_router)
app.include_router(attendance_router)
app.include_router(fees_router)
app.include_router(payments_router)
app.include_router(reports_router)
app.include_router(roles_permissions_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(audit_logs_router)
app.include_router(notifications_router)
app.include_router(search_router)
app.include_router(settings_router)
app.include_router(frontend_ui_router)
app.mount(
    "/assets",
    StaticFiles(directory=FRONTEND_DIST_DIR / "assets", check_dir=False),
    name="frontend-assets",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Student Management API"}


@app.get("/login", include_in_schema=False)
@app.get("/admin", include_in_schema=False)
@app.get("/admin/{path:path}", include_in_schema=False)
def read_react_spa() -> FileResponse:
    return FileResponse(FRONTEND_INDEX)
