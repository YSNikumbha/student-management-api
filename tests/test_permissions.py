"""Tests for role-based permissions and protected routes."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def test_get_students_without_auth(client: TestClient) -> None:
    """Test accessing students without auth returns 401."""
    response = client.get("/students")
    assert response.status_code == 401


def test_get_courses_without_auth(client: TestClient) -> None:
    """Test accessing courses without auth returns 401."""
    response = client.get("/courses")
    assert response.status_code == 401


def test_get_attendance_without_auth(client: TestClient) -> None:
    """Test accessing attendance without auth returns 401."""
    response = client.get("/attendance")
    assert response.status_code == 401


def test_get_fees_without_auth(client: TestClient) -> None:
    """Test accessing fees without auth returns 401."""
    response = client.get("/fees")
    assert response.status_code == 401


def test_get_dashboard_without_auth(client: TestClient) -> None:
    """Test accessing dashboard without auth returns 401."""
    response = client.get("/dashboard/summary")
    assert response.status_code == 401


def test_staff_can_read_students(client: TestClient, staff_headers: dict) -> None:
    """Test staff can read students."""
    response = client.get("/students", headers=staff_headers)
    assert response.status_code == 200


def test_staff_cannot_create_student(client: TestClient, staff_headers: dict, test_course) -> None:
    """Test staff cannot create student."""
    response = client.post(
        "/students",
        headers=staff_headers,
        json={
            "student_code": "STU999",
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user@test.com",
            "course_id": test_course.id,
        },
    )
    assert response.status_code == 403


def test_staff_cannot_delete_student(client: TestClient, staff_headers: dict, test_student) -> None:
    """Test staff cannot delete student."""
    response = client.delete(
        f"/students/{test_student.id}",
        headers=staff_headers,
    )
    assert response.status_code == 403


def test_admin_can_create_student(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test admin can create student."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU999",
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin.user@test.com",
            "course_id": test_course.id,
        },
    )
    assert response.status_code == 201


def test_admin_can_delete_student(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test admin can delete student."""
    response = client.delete(
        f"/students/{test_student.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


def test_staff_can_read_courses(client: TestClient, staff_headers: dict) -> None:
    """Test staff can read courses."""
    response = client.get("/courses", headers=staff_headers)
    assert response.status_code == 200


def test_staff_cannot_create_course(client: TestClient, staff_headers: dict) -> None:
    """Test staff cannot create course."""
    response = client.post(
        "/courses",
        headers=staff_headers,
        json={
            "code": "COURSE999",
            "name": "Test Course",
        },
    )
    assert response.status_code == 403


def test_staff_cannot_delete_course(client: TestClient, staff_headers: dict, test_course) -> None:
    """Test staff cannot delete course."""
    response = client.delete(
        f"/courses/{test_course.id}",
        headers=staff_headers,
    )
    assert response.status_code == 403


def test_staff_can_mark_attendance(client: TestClient, staff_headers: dict, test_student) -> None:
    """Test staff can mark attendance."""
    response = client.post(
        "/attendance",
        headers=staff_headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-15",
            "status": "present",
        },
    )
    assert response.status_code == 201


def test_staff_cannot_delete_attendance(client: TestClient, staff_headers: dict, test_student) -> None:
    """Test staff cannot delete attendance."""
    # First create attendance
    create_response = client.post(
        "/attendance",
        headers=staff_headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-15",
            "status": "present",
        },
    )
    assert create_response.status_code == 201
    attendance_id = create_response.json()["id"]
    
    # Try to delete
    response = client.delete(
        f"/attendance/{attendance_id}",
        headers=staff_headers,
    )
    assert response.status_code == 403


def test_admin_can_delete_attendance(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test admin can delete attendance."""
    # First create attendance
    create_response = client.post(
        "/attendance",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-15",
            "status": "present",
        },
    )
    assert create_response.status_code == 201
    attendance_id = create_response.json()["id"]
    
    # Delete
    response = client.delete(
        f"/attendance/{attendance_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204


def test_staff_can_view_fees(client: TestClient, staff_headers: dict) -> None:
    """Test staff can view fees."""
    response = client.get("/fees", headers=staff_headers)
    assert response.status_code == 200


def test_staff_can_record_payment(client: TestClient, staff_headers: dict, test_fee) -> None:
    """Test staff can record payment."""
    response = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=staff_headers,
        json={
            "amount": "1000.00",
            "payment_date": "2025-01-15",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 201


def test_staff_cannot_create_fee(client: TestClient, staff_headers: dict, test_student) -> None:
    """Test staff cannot create fee."""
    response = client.post(
        "/fees",
        headers=staff_headers,
        json={
            "student_id": test_student.id,
            "title": "Test Fee",
            "total_amount": "5000.00",
            "due_date": "2025-12-31",
        },
    )
    assert response.status_code == 403


def test_staff_cannot_delete_fee(client: TestClient, staff_headers: dict, test_fee) -> None:
    """Test staff cannot delete fee."""
    response = client.delete(
        f"/fees/{test_fee.id}",
        headers=staff_headers,
    )
    assert response.status_code == 403


def test_staff_can_view_but_not_edit_system_settings(
    client: TestClient,
    staff_headers: dict,
) -> None:
    """Test settings view/edit permissions are enforced by the backend."""
    read_response = client.get("/settings/system", headers=staff_headers)
    assert read_response.status_code == 200

    update_response = client.put(
        "/settings/system",
        headers=staff_headers,
        json={"school_name": "Updated Test School"},
    )
    assert update_response.status_code == 403


def test_teacher_cannot_view_system_settings_without_permission(
    client: TestClient,
    db: Session,
) -> None:
    """Test users without settings.view cannot read system settings."""
    teacher = User(
        name="Settings Teacher",
        email="settings.teacher@test.com",
        hashed_password=hash_password("TestPassword123!"),
        role="teacher",
        is_active=True,
    )
    db.add(teacher)
    db.commit()

    login_response = client.post(
        "/auth/login",
        json={"email": teacher.email, "password": "TestPassword123!"},
    )
    assert login_response.status_code == 200

    response = client.get(
        "/settings/system",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )
    assert response.status_code == 403
