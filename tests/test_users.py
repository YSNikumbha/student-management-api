from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


PASSWORD = "TestPassword123!"


def _create_role_user(db: Session, *, role: str, email: str) -> User:
    user = User(
        name=f"Test {role.title()}",
        email=email,
        hashed_password=hash_password(PASSWORD),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(client: TestClient, email: str, password: str = PASSWORD) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_can_manage_users(client: TestClient, admin_headers: dict) -> None:
    create_response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "New Teacher",
            "email": "new.teacher@test.com",
            "role": "teacher",
            "password": "Teacher123",
        },
    )
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["role"] == "teacher"
    assert "hashed_password" not in created_user
    user_id = created_user["id"]

    list_response = client.get("/users", headers=admin_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total_items"] >= 1

    detail_response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["email"] == "new.teacher@test.com"
    assert "hashed_password" not in detail_response.json()

    update_response = client.put(
        f"/users/{user_id}",
        headers=admin_headers,
        json={
            "name": "Updated Teacher",
            "email": "updated.teacher@test.com",
            "role": "teacher",
            "is_active": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Teacher"

    deactivate_response = client.patch(f"/users/{user_id}/deactivate", headers=admin_headers)
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False


def test_non_admin_cannot_manage_users(
    client: TestClient,
    test_db: Session,
) -> None:
    teacher = _create_role_user(test_db, role="teacher", email="teacher.users@test.com")
    accountant = _create_role_user(test_db, role="accountant", email="accountant.users@test.com")

    for user in (teacher, accountant):
        response = client.get("/users", headers=_headers_for(client, user.email))
        assert response.status_code == 403


def test_teacher_permissions(
    client: TestClient,
    test_db: Session,
    test_student,
) -> None:
    teacher = _create_role_user(test_db, role="teacher", email="teacher@test.com")
    headers = _headers_for(client, teacher.email)

    students_response = client.get("/students", headers=headers)
    assert students_response.status_code == 200

    attendance_response = client.post(
        "/attendance",
        headers=headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-15",
            "status": "present",
        },
    )
    assert attendance_response.status_code == 201

    fee_response = client.post(
        "/fees",
        headers=headers,
        json={
            "student_id": test_student.id,
            "title": "Teacher Forbidden Fee",
            "total_amount": "1000.00",
            "due_date": "2099-12-31",
        },
    )
    assert fee_response.status_code == 403


def test_accountant_permissions(
    client: TestClient,
    test_db: Session,
    test_student,
) -> None:
    accountant = _create_role_user(test_db, role="accountant", email="accountant@test.com")
    headers = _headers_for(client, accountant.email)

    students_response = client.get("/students", headers=headers)
    assert students_response.status_code == 200

    attendance_response = client.post(
        "/attendance",
        headers=headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-15",
            "status": "present",
        },
    )
    assert attendance_response.status_code == 403

    fee_response = client.post(
        "/fees",
        headers=headers,
        json={
            "student_id": test_student.id,
            "title": "Accountant Fee",
            "total_amount": "1000.00",
            "due_date": "2099-12-31",
        },
    )
    assert fee_response.status_code == 201

    fee_report_response = client.get("/reports/fees", headers=headers)
    assert fee_report_response.status_code == 200

    attendance_report_response = client.get("/reports/attendance", headers=headers)
    assert attendance_report_response.status_code == 403


def test_deactivated_user_cannot_login(client: TestClient, admin_headers: dict) -> None:
    create_response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "Inactive Teacher",
            "email": "inactive.teacher@test.com",
            "role": "teacher",
            "password": "Teacher123",
        },
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    deactivate_response = client.patch(f"/users/{user_id}/deactivate", headers=admin_headers)
    assert deactivate_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={"email": "inactive.teacher@test.com", "password": "Teacher123"},
    )
    assert login_response.status_code == 403


def test_admin_can_reset_password(client: TestClient, admin_headers: dict) -> None:
    create_response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "Reset Teacher",
            "email": "reset.teacher@test.com",
            "role": "teacher",
            "password": "Teacher123",
        },
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    reset_response = client.post(
        f"/users/{user_id}/reset-password",
        headers=admin_headers,
        json={"new_password": "Teacher456"},
    )
    assert reset_response.status_code == 200

    old_login_response = client.post(
        "/auth/login",
        json={"email": "reset.teacher@test.com", "password": "Teacher123"},
    )
    assert old_login_response.status_code == 401

    new_login_response = client.post(
        "/auth/login",
        json={"email": "reset.teacher@test.com", "password": "Teacher456"},
    )
    assert new_login_response.status_code == 200


def test_last_login_updates_after_successful_login(
    client: TestClient,
    test_db: Session,
) -> None:
    user = _create_role_user(test_db, role="teacher", email="last.login@test.com")
    assert user.last_login_at is None

    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["user"]["last_login_at"] is not None

    test_db.refresh(user)
    assert user.last_login_at is not None
