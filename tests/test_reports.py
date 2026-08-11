from datetime import date, datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.database.database import SessionLocal
from app.models.attendance import Attendance
from app.models.course import Course
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.user import User
from app.schemas.student import StudentCreate
from app.schemas.user import UserCreate
from app.services import course_service, student_service, user_service


def create_test_data(db: Session):
    course = course_service.create_course(db, course_service.CourseCreate(
        code="CS101",
        name="Computer Science",
        description="Test course",
        duration_months=12,
    ))

    admin = user_service.create_user(db, UserCreate(
        name="Admin User",
        email="admin@example.com",
        password="admin123",
        role="admin",
    ))

    staff = user_service.create_user(db, UserCreate(
        name="Staff User",
        email="staff@example.com",
        password="staff123",
        role="staff",
    ))

    student1 = student_service.create_student(db, StudentCreate(
        student_code="STU001",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="1234567890",
        course_id=course.id,
    ))

    student2 = student_service.create_student(db, StudentCreate(
        student_code="STU002",
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        phone="0987654321",
        course_id=course.id,
    ))

    fee1 = StudentFee(
        student_id=student1.id,
        title="Tuition Fee",
        description="Q1 tuition",
        total_amount=1000.00,
        due_date=date.today(),
        created_by=admin.id,
    )
    db.add(fee1)
    db.flush()

    payment = Payment(
        student_fee_id=fee1.id,
        amount=500.00,
        payment_date=date.today(),
        payment_method="cash",
        recorded_by=admin.id,
    )
    db.add(payment)

    attendance1 = Attendance(
        student_id=student1.id,
        date=date.today(),
        status="present",
        marked_by=admin.id,
    )
    attendance2 = Attendance(
        student_id=student2.id,
        date=date.today(),
        status="absent",
        marked_by=admin.id,
    )
    db.add(attendance1)
    db.add(attendance2)
    db.commit()

    return {
        "course": course,
        "admin": admin,
        "staff": staff,
        "student1": student1,
        "student2": student2,
        "fee1": fee1,
        "payment": payment,
    }


@pytest.fixture(scope="function")
def test_data(test_db):
    """Create test data for each test."""
    data = create_test_data(test_db)
    yield data


@pytest.fixture
def admin_token(client: TestClient, test_data):
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def staff_token(client: TestClient, test_data):
    response = client.post(
        "/auth/login",
        json={"email": "staff@example.com", "password": "staff123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def test_reports_require_authentication(client: TestClient):
    response = client.get("/reports/students")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_student_report_returns_filtered_students(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/students",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 2


def test_student_report_filters_by_course(client: TestClient, admin_token, test_data):
    response = client.get(
        f"/reports/students?course_id={test_data['course'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) >= 2


def test_student_report_filters_by_status(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/students?status=active",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(item["status"] == "active" for item in data["items"])


def test_attendance_report_calculations(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/attendance",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    for item in data["items"]:
        assert "attendance_percentage" in item
        assert 0 <= item["attendance_percentage"] <= 100


def test_attendance_report_detailed_mode(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/attendance?detail=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    if data["items"]:
        assert "date" in data["items"][0]
        assert "status" in data["items"][0]


def test_fee_report_balances(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/fees",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    for item in data["items"]:
        assert "balance" in item
        total = float(item["total_amount"])
        paid = float(item["paid_amount"])
        balance = float(item["balance"])
        assert balance == total - paid


def test_fee_report_status_filter(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/fees?status=partial",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(item["status"] == "partial" for item in data["items"])


def test_course_report_counts(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/courses",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    for item in data["items"]:
        assert "student_count" in item
        assert "active_student_count" in item
        assert item["active_student_count"] <= item["student_count"]


def test_csv_export_status_and_content_type(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/students/export/csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]
    assert "student_id" in response.text


def test_pdf_export_status_and_content_type(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/students/export/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "application/pdf" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert ".pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_date_range_validation(client: TestClient, admin_token):
    response = client.get(
        "/reports/attendance?start_date=2024-01-10&end_date=2024-01-09",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_staff_can_access_reports(client: TestClient, staff_token, test_data):
    response = client.get(
        "/reports/students",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == status.HTTP_200_OK


def test_staff_can_export_csv(client: TestClient, staff_token, test_data):
    response = client.get(
        "/reports/students/export/csv",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "text/csv" in response.headers["content-type"]


def test_staff_can_export_pdf(client: TestClient, staff_token, test_data):
    response = client.get(
        "/reports/students/export/pdf",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "application/pdf" in response.headers["content-type"]


def test_attendance_report_date_filter(client: TestClient, admin_token, test_data):
    today = date.today().isoformat()
    response = client.get(
        f"/reports/attendance?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) >= 2


def test_fee_report_due_date_filter(client: TestClient, admin_token, test_data):
    today = date.today().isoformat()
    response = client.get(
        f"/reports/fees?due_from={today}&due_to={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for item in data["items"]:
        assert today <= item["due_date"] <= today


def test_course_report_search(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/courses?search=Computer",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) >= 1
    assert "Computer" in data["items"][0]["course_name"]


def test_course_report_active_filter(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/courses?is_active=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(item["is_active"] is True for item in data["items"])


def test_attendance_csv_export(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/attendance/export/csv?detail=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "text/csv" in response.headers["content-type"]
    assert "date" in response.text


def test_fee_csv_export(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/fees/export/csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "text/csv" in response.headers["content-type"]
    assert "total_amount" in response.text


def test_course_csv_export(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/courses/export/csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "text/csv" in response.headers["content-type"]
    assert "student_count" in response.text


def test_attendance_pdf_export(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/attendance/export/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "application/pdf" in response.headers["content-type"]


def test_fee_pdf_export(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/fees/export/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "application/pdf" in response.headers["content-type"]


def test_course_pdf_export(client: TestClient, admin_token, test_data):
    response = client.get(
        "/reports/courses/export/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "application/pdf" in response.headers["content-type"]