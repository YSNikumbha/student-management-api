from fastapi import FastAPI

from app.routers.courses import router as courses_router
from app.routers.students import router as students_router

app = FastAPI(
    title="Student Management API",
    description="Backend API for managing students, courses, attendance, and fees.",
    version="1.0.0",
)

app.include_router(students_router)
app.include_router(courses_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Student Management API"}


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "healthy"}
