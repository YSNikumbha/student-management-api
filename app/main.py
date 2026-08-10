from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers.courses import router as courses_router
from app.routers.students import router as students_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Student Management API",
    description="Backend API for managing students, courses, attendance, and fees.",
    version="1.0.0",
)

app.include_router(students_router)
app.include_router(courses_router)
app.mount("/admin/assets", StaticFiles(directory=FRONTEND_DIR), name="admin-assets")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Student Management API"}


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/admin", include_in_schema=False)
def read_admin_dashboard() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/admin/students", include_in_schema=False)
def read_admin_students() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "students.html")


@app.get("/admin/courses", include_in_schema=False)
def read_admin_courses() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "courses.html")
