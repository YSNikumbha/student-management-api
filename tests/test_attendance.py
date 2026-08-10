"""Tests for attendance operations."""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient


def test_create_attendance(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test creating attendance record."""
    test_date = "2025-01-15"
    response = client.post(
        "/attendance",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "date": test_date,
            "status": "present",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == test_student.id
    assert data["date"] == test_date
    assert data["status"] == "present"
    assert "marked_by" in data


def test_create_attendance_duplicate(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test creating duplicate attendance returns 409."""
    test_date = "2025-01-16"
    attendance_data = {
        "student_id": test_student.id,
        "date": test_date,
        "status": "present",
    }
    
    # Create first attendance
    response1 = client.post("/attendance", headers=admin_headers, json=attendance_data)
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = client.post("/attendance", headers=admin_headers, json=attendance_data)
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"].lower()


def test_create_attendance_invalid_status(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test creating attendance with invalid status returns 422."""
    response = client.post(
        "/attendance",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-17",
            "status": "invalid_status",
        },
    )
    assert response.status_code == 422


def test_bulk_attendance(client: TestClient, admin_headers: dict, test_course_with_students) -> None:
    """Test bulk attendance marking."""
    test_date = "2025-01-18"
    students = test_course_with_students.students
    
    response = client.post(
        "/attendance/bulk",
        headers=admin_headers,
        json={
            "date": test_date,
            "records": [
                {
                    "student_id": students[0].id,
                    "status": "present",
                },
                {
                    "student_id": students[1].id,
                    "status": "absent",
                },
                {
                    "student_id": students[2].id,
                    "status": "late",
                },
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == test_date
    assert data["created"] == 3
    assert data["updated"] == 0
    assert len(data["records"]) == 3


def test_bulk_attendance_updates_existing(client: TestClient, admin_headers: dict, test_course_with_students) -> None:
    """Test bulk attendance updates existing records."""
    test_date = "2025-01-19"
    students = test_course_with_students.students
    
    # First bulk create
    response1 = client.post(
        "/attendance/bulk",
        headers=admin_headers,
        json={
            "date": test_date,
            "records": [
                {
                    "student_id": students[0].id,
                    "status": "present",
                },
            ],
        },
    )
    assert response1.status_code == 200
    assert response1.json()["created"] == 1
    
    # Second bulk update
    response2 = client.post(
        "/attendance/bulk",
        headers=admin_headers,
        json={
            "date": test_date,
            "records": [
                {
                    "student_id": students[0].id,
                    "status": "absent",
                },
            ],
        },
    )
    assert response2.status_code == 200
    assert response2.json()["created"] == 0
    assert response2.json()["updated"] == 1


def test_get_attendance_by_date(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test getting attendance by date."""
    test_date = "2025-01-20"
    
    # Create attendance
    client.post(
        "/attendance",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "date": test_date,
            "status": "present",
        },
    )
    
    # Get by date
    response = client.get(f"/attendance/date/{test_date}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["date"] == test_date


def test_get_student_attendance_summary(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test getting student attendance summary."""
    # Create multiple attendance records
    for i, status in enumerate(["present", "present", "absent", "late"], start=1):
        client.post(
            "/attendance",
            headers=admin_headers,
            json={
                "student_id": test_student.id,
                "date": f"2025-01-{i:02d}",
                "status": status,
            },
        )
    
    # Get summary
    response = client.get(f"/attendance/student/{test_student.id}/summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == test_student.id
    assert data["total_marked_days"] == 4
    assert data["present_days"] == 2
    assert data["absent_days"] == 1
    assert data["late_days"] == 1
    assert data["attendance_percentage"] == 50.0


def test_get_course_attendance_by_date(client: TestClient, admin_headers: dict, test_course_with_students) -> None:
    """Test getting course attendance by date."""
    test_date = "2025-01-21"
    students = test_course_with_students.students
    
    # Mark attendance for all students
    for student in students:
        client.post(
            "/attendance",
            headers=admin_headers,
            json={
                "student_id": student.id,
                "date": test_date,
                "status": "present",
            },
        )
    
    # Get course attendance
    response = client.get(
        f"/attendance/course/{test_course_with_students.id}/date/{test_date}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["course_id"] == test_course_with_students.id
    assert data["date"] == test_date
    assert len(data["students"]) == 3


def test_update_attendance(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test updating attendance."""
    # Create attendance
    create_response = client.post(
        "/attendance",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-22",
            "status": "present",
        },
    )
    assert create_response.status_code == 201
    attendance_id = create_response.json()["id"]
    
    # Update attendance
    update_response = client.put(
        f"/attendance/{attendance_id}",
        headers=admin_headers,
        json={
            "status": "absent",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "absent"


def test_delete_attendance(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test deleting attendance."""
    # Create attendance
    create_response = client.post(
        "/attendance",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "date": "2025-01-23",
            "status": "present",
        },
    )
    assert create_response.status_code == 201
    attendance_id = create_response.json()["id"]
    
    # Delete
    response = client.delete(f"/attendance/{attendance_id}", headers=admin_headers)
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(f"/attendance/{attendance_id}", headers=admin_headers)
    assert get_response.status_code == 404


def test_attendance_pagination(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test attendance pagination."""
    # Create multiple attendance records
    for i in range(5):
        client.post(
            "/attendance",
            headers=admin_headers,
            json={
                "student_id": test_student.id,
                "date": f"2025-01-{i+1:02d}",
                "status": "present",
            },
        )
    
    # Get with pagination
    response = client.get("/attendance?page=1&page_size=2", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_items" in data
    assert len(data["items"]) <= 2