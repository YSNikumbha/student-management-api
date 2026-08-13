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
from app.services import academic_year_service, batch_service, course_service, semester_service, student_service, subject_service, user_service, attendance_session_service


def create_test_data(db: Session):
    from app.models.academic_year import AcademicYear
    from app.models.semester import Semester
    from app.models.batch import Batch
    from app.models.attendance_session import AttendanceSession
    from app.models.academic_performance import Assessment, StudentResult
    from app.schemas.academic_year import AcademicYearCreate
    from app.schemas.semester import SemesterCreate
    from app.schemas.batch import BatchCreate
    from app.schemas.subject import SubjectCreate
    from app.schemas.attendance_session import AttendanceSessionCreate
    
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

    # Create academic structure for attendance sessions
    academic_year = academic_year_service.create_academic_year(
        db, 
        AcademicYearCreate(
            name="2025-26",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 5, 31),
        )
    )
    
    semester = semester_service.create_semester(
        db,
        SemesterCreate(
            academic_year_id=academic_year.id,
            course_id=course.id,
            number=1,
            name="Semester 1",
        ),
    )
    
    batch = batch_service.create_batch(
        db,
        BatchCreate(
            name="CS-2025-A",
            course_id=course.id,
            academic_year_id=academic_year.id,
            capacity=30,
        ),
    )
    
    # Create subject
    subject = subject_service.create_subject(
        db,
        SubjectCreate(
            course_id=course.id,
            semester_id=semester.id,
            code="CS101",
            name="Introduction to Programming",
        ),
    )
    db.commit()
    student1.batch_id = batch.id
    student1.academic_year_id = academic_year.id
    student1.semester_id = semester.id
    student2.batch_id = batch.id
    student2.academic_year_id = academic_year.id
    student2.semester_id = semester.id
    db.commit()
    
    # Create attendance session
    session = attendance_session_service.create_attendance_session(
        db,
        AttendanceSessionCreate(
            course_id=course.id,
            batch_id=batch.id,
            semester_id=semester.id,
            subject_id=subject.id,
            date=datetime.now(),
            session_name="Test Session",
        ),
        created_by=admin.id,
    )
    db.commit()
    
    # Create attendance records linked to session
    attendance1 = Attendance(
        attendance_session_id=session.id,
        student_id=student1.id,
        status="present",
        marked_by=admin.id,
    )
    attendance2 = Attendance(
        attendance_session_id=session.id,
        student_id=student2.id,
        status="absent",
        marked_by=admin.id,
    )
    db.add(attendance1)
    db.add(attendance2)
    assessment = Assessment(
        name="Demo Test Assessment",
        subject_id=subject.id,
        semester_id=semester.id,
        academic_year_id=academic_year.id,
        assessment_type="Mid Term",
        max_marks=100,
        weight_percentage=1,
        date=date(2026, 8, 12),
    )
    db.add(assessment)
    db.flush()
    db.add(StudentResult(assessment_id=assessment.id, student_id=student1.id, marks_obtained=91, grade="A+"))
    db.add(StudentResult(assessment_id=assessment.id, student_id=student2.id, marks_obtained=72, grade="B+"))
    db.commit()

    return {
        "course": course,
        "admin": admin,
        "staff": staff,
        "student1": student1,
        "student2": student2,
        "fee1": fee1,
        "payment": payment,
        "batch": batch,
        "subject": subject,
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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "query",
    [
        "period=daily&date=2026-08-12",
        "period=monthly&year=2026&month=8",
        "period=yearly&year=2026",
        "period=custom&from_date=2026-08-01&to_date=2026-08-31",
    ],
)
def test_attendance_period_filters(client: TestClient, admin_token, test_data, query):
    response = client.get(
        f"/reports/attendance?{query}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "summary" in body
    assert "filters" in body


@pytest.mark.parametrize(
    "query,detail",
    [
        ("period=monthly&year=2026&month=13", None),
        ("period=daily", "date is required"),
        ("period=yearly", "year is required"),
        ("period=custom&from_date=2026-09-01&to_date=2026-08-01", "from_date"),
    ],
)
def test_invalid_report_filters(client: TestClient, admin_token, query, detail):
    response = client.get(
        f"/reports/attendance?{query}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_invalid_class_and_student_filters(client: TestClient, admin_token, test_data, test_db):
    response = client.get(
        "/reports/attendance?class_id=999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response = client.get(
        "/reports/attendance?student_id=999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    from app.models.batch import Batch

    other_batch = Batch(
        name="OTHER-CLASS",
        course_id=test_data["course"].id,
        academic_year_id=test_data["batch"].academic_year_id,
        semester_id=test_data["batch"].semester_id,
    )
    test_db.add(other_batch)
    test_db.commit()
    response = client.get(
        f"/reports/attendance?class_id={other_batch.id}&student_id={test_data['student1'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_specific_student_and_class_reports(client: TestClient, admin_token, test_data):
    student_response = client.get(
        f"/reports/attendance?student_id={test_data['student1'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert student_response.status_code == status.HTTP_200_OK
    assert all(item["student_id"] == test_data["student1"].id for item in student_response.json()["items"])

    class_response = client.get(
        f"/reports/attendance?class_id={test_data['batch'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert class_response.status_code == status.HTTP_200_OK
    assert class_response.json()["total"] >= 2


def test_academic_and_top_performer_filters(client: TestClient, admin_token, test_data):
    response = client.get(
        f"/reports/academic?period=yearly&year=2026&class_id={test_data['batch'].id}&subject_id={test_data['subject'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["top_students"]

    response = client.get(
        f"/reports/top-performers?top_n=5&subject_id={test_data['subject'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] <= 5


def test_filtered_csv_and_pdf_exports(client: TestClient, admin_token, test_data):
    csv_response = client.get(
        f"/reports/attendance/export/csv?class_id={test_data['batch'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert csv_response.status_code == status.HTTP_200_OK
    assert "text/csv" in csv_response.headers["content-type"]
    assert "excused_days" in csv_response.text

    pdf_response = client.get(
        f"/reports/fees/export/pdf?student_id={test_data['student1'].id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pdf_response.status_code == status.HTTP_200_OK
    assert pdf_response.content.startswith(b"%PDF")


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
