"""Tests for basic health and API endpoints."""

from fastapi.testclient import TestClient

from app.database.database import get_db
from app.main import app


def test_read_root(client: TestClient) -> None:
    """Test root endpoint returns 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Student Management API"}


def test_read_health(client: TestClient) -> None:
    """Test health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_read_liveness(client: TestClient) -> None:
    """Test liveness endpoint returns process health."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_uses_database(client: TestClient) -> None:
    """Test readiness endpoint verifies database connectivity."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_hides_database_errors() -> None:
    """Test readiness endpoint returns a safe 503 on database failure."""
    class BrokenSession:
        def execute(self, _statement):
            raise RuntimeError("connection password leaked here")

    def override_get_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as broken_client:
            response = broken_client.get("/health/ready")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not ready"}


def test_docs_endpoint(client: TestClient) -> None:
    """Test docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
