from fastapi import FastAPI

from app.database.base import Base
from app.database.database import engine

# Import models so their tables are registered on Base.metadata.
from app.models.student import Student  # noqa: F401


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Student Management API",
    description="Backend API for managing students, courses, attendance, and fees.",
    version="1.0.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Student Management API"}


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "healthy"}
