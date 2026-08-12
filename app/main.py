from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers.academic_years import router as academic_years_router
from app.routers.attendance import router as attendance_router
from app.routers.attendance_sessions import router as attendance_sessions_router
from app.routers.auth import router as auth_router
from app.routers.batches import router as batches_router
from app.routers.courses import router as courses_router
from app.routers.dashboard import router as dashboard_router
from app.routers.fees import router as fees_router
from app.routers.payments import router as payments_router
from app.routers.reports import router as reports_router
from app.routers.semesters import router as semesters_router
from app.routers.students import router as students_router
from app.routers.subjects import router as subjects_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Student Management API",
    description="Backend API for managing students, courses, attendance, and fees.",
    version="1.0.0",
)


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "healthy"}

app.include_router(auth_router)
app.include_router(academic_years_router)
app.include_router(semesters_router)
app.include_router(subjects_router)
app.include_router(batches_router)
app.include_router(students_router)
app.include_router(courses_router)
app.include_router(attendance_sessions_router)
app.include_router(attendance_router)
app.include_router(fees_router)
app.include_router(payments_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
app.mount("/admin/assets", StaticFiles(directory=FRONTEND_DIR), name="admin-assets")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Student Management API"}


@app.get("/admin", include_in_schema=False)
def read_admin_dashboard() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/admin/students", include_in_schema=False)
def read_admin_students() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "students.html")


@app.get("/admin/courses", include_in_schema=False)
def read_admin_courses() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "courses.html")


@app.get("/admin/attendance", include_in_schema=False)
def read_admin_attendance() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "attendance.html")


@app.get("/admin/fees", include_in_schema=False)
def read_admin_fees() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "fees.html")


@app.get("/admin/reports", include_in_schema=False)
def read_admin_reports() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "reports.html")


@app.get("/login", include_in_schema=False)
def read_login() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "login.html")
