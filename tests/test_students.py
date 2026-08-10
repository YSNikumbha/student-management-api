"""Tests for student CRUD operations."""

from fastapi.testclient import TestClient


def test_admin_can_create_student(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test admin can create a student."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU100",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice.smith@test.com",
            "phone": "1234567890",
            "course_id": test_course.id,
            "status": "active",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["student_code"] == "STU100"
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"
    assert data["email"] == "alice.smith@test.com"
    assert data["status"] == "active"
    assert "id" in data


def test_create_student_duplicate_email(client: TestClient, admin_headers: dict, test_course, test_student) -> None:
    """Test creating student with duplicate email returns 409."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU200",
            "first_name": "Bob",
            "last_name": "Jones",
            "email": test_student.email,  # duplicate
            "course_id": test_course.id,
        },
    )
    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


def test_create_student_duplicate_code(client: TestClient, admin_headers: dict, test_course, test_student) -> None:
    """Test creating student with duplicate code returns 409."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": test_student.student_code,  # duplicate
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob.jones@test.com",
            "course_id": test_course.id,
        },
    )
    assert response.status_code == 409
    assert "student code" in response.json()["detail"].lower()


def test_create_student_invalid_course(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with invalid course_id returns 404."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU300",
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie@test.com",
            "course_id": 99999,  # non-existent
        },
    )
    assert response.status_code == 404
    assert "Course not found" in response.json()["detail"]


def test_get_student_by_id(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test getting a student by ID."""
    response = client.get(f"/students/{test_student.id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_student.id
    assert data["student_code"] == test_student.student_code


def test_get_student_not_found(client: TestClient, admin_headers: dict) -> None:
    """Test getting non-existent student returns 404."""
    response = client.get("/students/99999", headers=admin_headers)
    assert response.status_code == 404
    assert "Student not found" in response.json()["detail"]


def test_get_students_pagination(client: TestClient, admin_headers: dict, test_course_with_students) -> None:
    """Test getting students with pagination."""
    response = client.get("/students?page=1&page_size=2", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_items" in data
    assert "total_pages" in data
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) <= 2


def test_update_student(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test updating a student."""
    response = client.put(
        f"/students/{test_student.id}",
        headers=admin_headers,
        json={
            "phone": "9876543210",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "9876543210"


def test_update_student_duplicate_email(client: TestClient, admin_headers: dict, test_student, test_course) -> None:
    """Test updating student with duplicate email returns 409."""
    # Create another student
    create_response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU_NEW",
            "first_name": "New",
            "last_name": "Student",
            "email": "new.student@test.com",
            "course_id": test_course.id,
        },
    )
    assert create_response.status_code == 201
    new_student = create_response.json()
    
    # Try to update test_student with new student's email
    response = client.put(
        f"/students/{test_student.id}",
        headers=admin_headers,
        json={
            "email": "new.student@test.com",
        },
    )
    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


def test_delete_student(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test deleting a student."""
    response = client.delete(f"/students/{test_student.id}", headers=admin_headers)
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(f"/students/{test_student.id}", headers=admin_headers)
    assert get_response.status_code == 404


def test_search_students(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test searching students."""
    # Create test students
    client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "SEARCH1",
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice@test.com",
            "course_id": test_course.id,
        },
    )
    
    response = client.get("/students?search=Alice", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 1
    assert any(student["first_name"] == "Alice" for student in data["items"])


def test_filter_students_by_status(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test filtering students by status."""
    response = client.get("/students?status=active", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 1
    for student in data["items"]:
        assert student["status"] == "active"


def test_sort_students(client: TestClient, admin_headers: dict, test_course) -> None:
    """Test sorting students."""
    response = client.get("/students?sort_by=first_name&sort_order=asc", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    names = [student["first_name"] for student in data["items"]]
    assert names == sorted(names)