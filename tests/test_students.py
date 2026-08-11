"""Tests for student CRUD operations."""

from datetime import date, timedelta

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


# ============================================
# VALIDATION TESTS
# ============================================

def test_create_student_blank_code(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with blank student code returns 422."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "   ",  # blank only
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
        },
    )
    assert response.status_code == 422
    assert "student code" in response.json()["detail"][0]["msg"].lower()


def test_create_student_invalid_code_too_short(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with student code too short returns 422."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "A",  # too short
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
        },
    )
    assert response.status_code == 422
    assert "student code" in response.json()["detail"][0]["msg"].lower()


def test_create_student_invalid_code_characters(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with invalid characters in code returns 422."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU@123!",  # invalid characters
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
        },
    )
    assert response.status_code == 422
    assert "student code" in response.json()["detail"][0]["msg"].lower()


def test_create_student_lowercase_code_normalized(client: TestClient, admin_headers: dict) -> None:
    """Test that lowercase student code is normalized to uppercase."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "stu100",  # lowercase
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice.normalized@test.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["student_code"] == "STU100"  # should be uppercase


def test_create_student_invalid_short_name(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with name too short returns 422."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU400",
            "first_name": "A",  # too short
            "last_name": "Smith",
            "email": "alice@test.com",
        },
    )
    assert response.status_code == 422
    assert "name" in response.json()["detail"][0]["msg"].lower()


def test_create_student_invalid_phone(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with invalid phone returns 422."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU500",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
            "phone": "123",  # too short
        },
    )
    assert response.status_code == 422
    assert "phone" in response.json()["detail"][0]["msg"].lower()


def test_create_student_phone_with_letters(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with alphabetic phone returns 422."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU501",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
            "phone": "123abc4567",  # contains letters
        },
    )
    assert response.status_code == 422
    assert "phone" in response.json()["detail"][0]["msg"].lower()


def test_create_student_future_dob(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with future date of birth returns 422."""
    future_date = date.today() + timedelta(days=1)
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU600",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
            "date_of_birth": future_date.isoformat(),
        },
    )
    assert response.status_code == 422
    assert "date of birth" in response.json()["detail"][0]["msg"].lower()


def test_create_student_invalid_status(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with invalid status returns 422."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU700",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
            "status": "invalid_status",  # invalid status
        },
    )
    assert response.status_code == 422


def test_create_student_valid_edge_cases(client: TestClient, admin_headers: dict) -> None:
    """Test creating student with valid edge cases."""
    # Test with minimum length code
    response1 = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "AB",  # minimum 2 chars
            "first_name": "Jo",  # minimum 2 chars
            "last_name": "Do",
            "email": "jo.do@test.com",
        },
    )
    assert response1.status_code == 201
    
    # Test with name containing apostrophe and hyphen
    response2 = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU800",
            "first_name": "Mary-Jane",
            "last_name": "O'Connor",
            "email": "mary.jane@test.com",
        },
    )
    assert response2.status_code == 201
    
    # Test with phone including country code
    response3 = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU900",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice.intl@test.com",
            "phone": "+14155551234",
        },
    )
    assert response3.status_code == 201
    data3 = response3.json()
    assert data3["phone"] == "+14155551234"


def test_update_student_code_normalization(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test updating student code normalizes to uppercase."""
    response = client.put(
        f"/students/{test_student.id}",
        headers=admin_headers,
        json={
            "student_code": "newcode123",  # lowercase
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["student_code"] == "NEWCODE123"


def test_update_student_trim_whitespace(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test updating student trims whitespace from names."""
    response = client.put(
        f"/students/{test_student.id}",
        headers=admin_headers,
        json={
            "first_name": "  Alice  ",  # with whitespace
            "last_name": "  Smith  ",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"


def test_create_student_email_lowercase_normalization(client: TestClient, admin_headers: dict) -> None:
    """Test that email is normalized to lowercase."""
    response = client.post(
        "/students",
        headers=admin_headers,
        json={
            "student_code": "STU_EMAIL",
            "first_name": "Test",
            "last_name": "User",
            "email": "TEST.USER@EXAMPLE.COM",  # uppercase
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test.user@example.com"  # should be lowercase