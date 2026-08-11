"""Tests for course CRUD operations."""

from fastapi.testclient import TestClient


def test_admin_can_create_course(client: TestClient, admin_headers: dict) -> None:
    """Test admin can create a course."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "COURSE101",
            "name": "Introduction to Python",
            "description": "Learn Python programming",
            "duration_months": 3,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "COURSE101"
    assert data["name"] == "Introduction to Python"
    assert "id" in data


def test_create_course_duplicate_code(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test creating course with duplicate code returns 409."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": test_course.code,  # duplicate
            "name": "Another Course",
        },
    )
    assert response.status_code == 409
    assert "code" in response.json()["detail"].lower()


def test_get_courses(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test getting all courses."""
    response = client.get("/courses", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total_items"] >= 1


def test_get_course_by_id(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test getting a course by ID."""
    response = client.get(f"/courses/{test_course.id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_course.id
    assert data["code"] == test_course.code


def test_get_course_not_found(client: TestClient, admin_headers: dict) -> None:
    """Test getting non-existent course returns 404."""
    response = client.get("/courses/99999", headers=admin_headers)
    assert response.status_code == 404
    assert "Course not found" in response.json()["detail"]


def test_update_course(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test updating a course."""
    response = client.put(
        f"/courses/{test_course.id}",
        headers=admin_headers,
        json={
            "name": "Updated Course Name",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Course Name"


def test_delete_course_success(client: TestClient, admin_headers: dict) -> None:
    """Test deleting an unused course."""
    # Create a new course without students
    create_response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "DELETE_ME",
            "name": "Course to Delete",
        },
    )
    assert create_response.status_code == 201
    course_id = create_response.json()["id"]
    
    # Delete it
    response = client.delete(f"/courses/{course_id}", headers=admin_headers)
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(f"/courses/{course_id}", headers=admin_headers)
    assert get_response.status_code == 404


def test_delete_course_with_students_fails(client: TestClient, admin_headers: dict, test_course_with_students) -> None:
    """Test deleting course with students returns 409."""
    response = client.delete(
        f"/courses/{test_course_with_students.id}",
        headers=admin_headers,
    )
    assert response.status_code == 409
    assert "students are assigned" in response.json()["detail"].lower()


def test_search_courses(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test searching courses."""
    response = client.get(f"/courses?search={test_course.code}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 1
    assert any(course["code"] == test_course.code for course in data["items"])


def test_filter_courses_by_active(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test filtering courses by active status."""
    response = client.get("/courses?is_active=true", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 1
    for course in data["items"]:
        assert course["is_active"] is True


def test_course_pagination(client: TestClient, admin_headers: dict) -> None:
    """Test course pagination."""
    response = client.get("/courses?page=1&page_size=5", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_items" in data
    assert "total_pages" in data


def test_create_course_invalid_code(client: TestClient, admin_headers: dict) -> None:
    """Test creating course with invalid code returns 422."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "INVALID@CODE!",
            "name": "Valid Course Name",
        },
    )
    assert response.status_code == 422
    assert "code" in response.json()["detail"][0]["msg"].lower()


def test_create_course_blank_name(client: TestClient, admin_headers: dict) -> None:
    """Test creating course with blank name returns 422."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "COURSE1",
            "name": "   ",
        },
    )
    assert response.status_code == 422
    assert "name" in response.json()["detail"][0]["msg"].lower()


def test_create_course_name_too_short(client: TestClient, admin_headers: dict) -> None:
    """Test creating course with name too short returns 422."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "COURSE1",
            "name": "AB",
        },
    )
    assert response.status_code == 422
    assert "name" in response.json()["detail"][0]["msg"].lower()


def test_create_course_duration_zero(client: TestClient, admin_headers: dict) -> None:
    """Test creating course with duration 0 returns 422."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "COURSE1",
            "name": "Valid Course Name",
            "duration_months": 0,
        },
    )
    assert response.status_code == 422
    assert "duration" in response.json()["detail"][0]["msg"].lower()


def test_create_course_duration_negative(client: TestClient, admin_headers: dict) -> None:
    """Test creating course with negative duration returns 422."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "COURSE1",
            "name": "Valid Course Name",
            "duration_months": -3,
        },
    )
    assert response.status_code == 422
    assert "duration" in response.json()["detail"][0]["msg"].lower()


def test_create_course_duration_too_large(client: TestClient, admin_headers: dict) -> None:
    """Test creating course with duration > 120 months returns 422."""
    response = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "COURSE1",
            "name": "Valid Course Name",
            "duration_months": 121,
        },
    )
    assert response.status_code == 422
    assert "duration" in response.json()["detail"][0]["msg"].lower()


def test_create_course_valid_edge_cases(client: TestClient, admin_headers: dict) -> None:
    """Test creating course with valid edge cases."""
    # Test with minimum length code and name
    response1 = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "AB",
            "name": "ABC",
            "description": "A" * 500,
            "duration_months": 120,
            "is_active": True,
        },
    )
    assert response1.status_code == 201
    data1 = response1.json()
    assert data1["code"] == "AB"
    assert data1["name"] == "ABC"
    assert data1["duration_months"] == 120

    # Test code normalization to uppercase
    response2 = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "lowercase",
            "name": "Lowercase Code Test",
        },
    )
    assert response2.status_code == 201
    data2 = response2.json()
    assert data2["code"] == "LOWERCASE"

    # Test optional fields
    response3 = client.post(
        "/courses",
        headers=admin_headers,
        json={
            "code": "MINIMAL",
            "name": "Minimal Course",
        },
    )
    assert response3.status_code == 201
    data3 = response3.json()
    assert data3["description"] is None
    assert data3["duration_months"] is None
