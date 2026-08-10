"""Tests for dashboard endpoints."""

from datetime import date

from fastapi.testclient import TestClient


def test_get_dashboard_summary(client: TestClient, admin_headers: dict, test_student, test_course, test_fee) -> None:
    """Test getting dashboard summary."""
    response = client.get("/dashboard/summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "students" in data
    assert "courses" in data
    assert "attendance_today" in data
    assert "fees" in data
    
    # Verify student stats
    assert "total" in data["students"]
    assert "active" in data["students"]
    assert "inactive" in data["students"]
    assert data["students"]["total"] >= 1
    
    # Verify course stats
    assert "total" in data["courses"]
    assert "active" in data["courses"]
    assert data["courses"]["total"] >= 1
    
    # Verify fee stats
    assert "total_assigned" in data["fees"]
    assert "total_collected" in data["fees"]
    assert "total_pending" in data["fees"]
    assert "overdue_count" in data["fees"]


def test_get_recent_activity(client: TestClient, admin_headers: dict, test_student, test_fee) -> None:
    """Test getting recent activity."""
    response = client.get("/dashboard/recent-activity", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "recent_students" in data
    assert "recent_payments" in data
    assert "recent_attendance" in data
    
    # Verify recent students
    assert isinstance(data["recent_students"], list)
    assert len(data["recent_students"]) >= 1
    
    # Verify recent payments
    assert isinstance(data["recent_payments"], list)
    
    # Verify recent attendance
    assert isinstance(data["recent_attendance"], list)


def test_get_course_stats(client: TestClient, admin_headers: dict, test_course_with_students) -> None:
    """Test getting course statistics."""
    response = client.get("/dashboard/course-stats", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Verify course stat structure
    course_stat = data[0]
    assert "course_id" in course_stat
    assert "course_code" in course_stat
    assert "course_name" in course_stat
    assert "student_count" in course_stat
    assert course_stat["student_count"] >= 0


def test_dashboard_requires_auth(client: TestClient) -> None:
    """Test dashboard endpoints require authentication."""
    response = client.get("/dashboard/summary")
    assert response.status_code == 401
    
    response = client.get("/dashboard/recent-activity")
    assert response.status_code == 401
    
    response = client.get("/dashboard/course-stats")
    assert response.status_code == 401