from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


PASSWORD = "TestPassword123!"


def _create_user(db: Session, *, role: str, email: str) -> User:
    user = User(
        name=f"Audit {role.title()}",
        email=email,
        hashed_password=hash_password(PASSWORD),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_student_create_writes_audit_log(
    client: TestClient,
    admin_headers: dict,
    test_course,
) -> None:
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "AUD001",
            "first_name": "Audit",
            "last_name": "Student",
            "email": "audit.student@test.com",
            "course_id": test_course.id,
        },
    )
    assert response.status_code == 201

    logs_response = client.get(
        "/audit-logs?action=student_created&entity_type=student",
        headers=admin_headers,
    )
    assert logs_response.status_code == 200
    logs = logs_response.json()["items"]
    assert any(log["entity_id"] == str(response.json()["id"]) for log in logs)


def test_user_role_change_and_deactivation_write_audit_logs(
    client: TestClient,
    admin_headers: dict,
) -> None:
    create_response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "Audit Teacher",
            "email": "audit.teacher@test.com",
            "role": "teacher",
            "password": "Teacher123",
        },
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    update_response = client.put(
        f"/users/{user_id}",
        headers=admin_headers,
        json={
            "name": "Audit Accountant",
            "email": "audit.teacher@test.com",
            "role": "accountant",
            "is_active": True,
        },
    )
    assert update_response.status_code == 200

    deactivate_response = client.patch(f"/users/{user_id}/deactivate", headers=admin_headers)
    assert deactivate_response.status_code == 200

    role_logs = client.get("/audit-logs?action=role_changed", headers=admin_headers)
    assert role_logs.status_code == 200
    assert any(log["entity_id"] == str(user_id) for log in role_logs.json()["items"])

    deactivation_logs = client.get("/audit-logs?action=user_deactivated", headers=admin_headers)
    assert deactivation_logs.status_code == 200
    assert any(log["entity_id"] == str(user_id) for log in deactivation_logs.json()["items"])


def test_audit_metadata_does_not_store_password(
    client: TestClient,
    admin_headers: dict,
) -> None:
    response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "Audit Secret",
            "email": "audit.secret@test.com",
            "role": "teacher",
            "password": "Teacher123",
        },
    )
    assert response.status_code == 201

    logs_response = client.get("/audit-logs?action=user_created", headers=admin_headers)
    assert logs_response.status_code == 200
    for log in logs_response.json()["items"]:
        metadata = log.get("metadata_json") or {}
        assert "password" not in metadata
        assert "hashed_password" not in metadata


def test_non_admin_roles_cannot_access_audit_logs(
    client: TestClient,
    test_db: Session,
) -> None:
    for role in ("staff", "teacher", "accountant"):
        user = _create_user(test_db, role=role, email=f"audit.{role}@test.com")
        response = client.get("/audit-logs", headers=_headers(client, user.email))
        assert response.status_code == 403
