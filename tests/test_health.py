"""Tests for basic health and API endpoints."""

from fastapi.testclient import TestClient


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


def test_docs_endpoint(client: TestClient) -> None:
    """Test docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200