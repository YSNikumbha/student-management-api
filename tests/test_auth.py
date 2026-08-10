"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient


def test_admin_login_success(client: TestClient, admin_user) -> None:
    """Test successful admin login returns token."""
    response = client.post(
        "/auth/login",
        json={
            "email": admin_user.email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == admin_user.email
    assert data["user"]["role"] == "admin"


def test_staff_login_success(client: TestClient, staff_user) -> None:
    """Test successful staff login returns token."""
    response = client.post(
        "/auth/login",
        json={
            "email": staff_user.email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == staff_user.email
    assert data["user"]["role"] == "staff"


def test_login_wrong_password(client: TestClient, admin_user) -> None:
    """Test login with wrong password returns 401."""
    response = client.post(
        "/auth/login",
        json={
            "email": admin_user.email,
            "password": "WrongPassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client: TestClient) -> None:
    """Test login with unknown email returns 401."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_inactive_user(client: TestClient, inactive_user) -> None:
    """Test login with inactive user returns 403."""
    response = client.post(
        "/auth/login",
        json={
            "email": inactive_user.email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "This account is inactive"


def test_login_missing_fields(client: TestClient) -> None:
    """Test login with missing fields returns 422."""
    response = client.post(
        "/auth/login",
        json={"email": "test@test.com"},
    )
    assert response.status_code == 422