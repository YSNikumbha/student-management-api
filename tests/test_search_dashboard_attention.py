from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.academic_year import AcademicYear
from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession
from app.models.batch import Batch
from app.models.payment import Payment
from app.models.semester import Semester
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.subject import Subject
from app.models.user import User


def _academic_setup(db: Session, course):
    year = AcademicYear(
        name="SEARCH-2026",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db.add(year)
    db.commit()
    db.refresh(year)

    semester = Semester(
        academic_year_id=year.id,
        course_id=course.id,
        number=1,
        name="Search Semester",
        is_active=True,
    )
    db.add(semester)
    db.commit()
    db.refresh(semester)

    subject = Subject(
        course_id=course.id,
        semester_id=semester.id,
        code="DBMS501",
        name="Database Management Systems",
        is_active=True,
    )
    batch = Batch(
        name="SEARCH-BATCH-A",
        course_id=course.id,
        academic_year_id=year.id,
        semester_id=semester.id,
        is_active=True,
    )
    db.add_all([subject, batch])
    db.commit()
    db.refresh(subject)
    db.refresh(batch)
    return year, semester, subject, batch


def _headers_for_staff(client: TestClient, db: Session) -> dict[str, str]:
    staff = User(
        name="Search Staff",
        email="search.staff@test.com",
        hashed_password=hash_password("TestPassword123!"),
        role="staff",
        is_active=True,
    )
    db.add(staff)
    db.commit()
    response = client.post(
        "/auth/login",
        json={"email": staff.email, "password": "TestPassword123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_global_search_requires_auth(client: TestClient) -> None:
    response = client.get("/search?q=john")
    assert response.status_code == 401


def test_global_search_relevance_and_admin_users(
    client: TestClient,
    admin_headers: dict,
    test_db: Session,
    test_course,
    test_student,
) -> None:
    _academic_setup(test_db, test_course)

    response = client.get("/search?q=Database", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert any(item["title"] == "Database Management Systems" for item in data["subjects"])

    student_response = client.get("/search?q=John", headers=admin_headers)
    assert student_response.status_code == 200
    assert any(item["id"] == test_student.id for item in student_response.json()["students"])

    course_response = client.get("/search?q=TEST101", headers=admin_headers)
    assert course_response.status_code == 200
    assert any(item["id"] == test_course.id for item in course_response.json()["courses"])

    batch_response = client.get("/search?q=SEARCH-BATCH", headers=admin_headers)
    assert batch_response.status_code == 200
    assert any(item["title"] == "SEARCH-BATCH-A" for item in batch_response.json()["batches"])

    admin_user_response = client.get("/search?q=admin@test.com", headers=admin_headers)
    assert admin_user_response.status_code == 200
    assert any(item["type"] == "user" for item in admin_user_response.json()["users"])


def test_global_search_hides_users_for_non_admin(
    client: TestClient,
    test_db: Session,
) -> None:
    staff_headers = _headers_for_staff(client, test_db)
    response = client.get("/search?q=admin@test.com", headers=staff_headers)
    assert response.status_code == 200
    assert response.json()["users"] == []


def test_dashboard_attention_queries(
    client: TestClient,
    admin_headers: dict,
    test_db: Session,
    admin_user: User,
    test_course,
    test_student: Student,
) -> None:
    year, semester, subject, batch = _academic_setup(test_db, test_course)
    test_student.academic_year_id = year.id
    test_student.semester_id = semester.id
    test_student.batch_id = batch.id
    test_student.admission_date = date.today()

    for idx, status in enumerate(["present", "absent", "absent"], start=1):
        test_db.add(
            Attendance(
                student_id=test_student.id,
                date=date.today() - timedelta(days=idx),
                status=status,
                marked_by=admin_user.id,
            )
        )

    overdue_fee = StudentFee(
        student_id=test_student.id,
        title="Overdue Attention Fee",
        total_amount=Decimal("1000.00"),
        due_date=date.today() - timedelta(days=1),
        created_by=admin_user.id,
    )
    due_soon_fee = StudentFee(
        student_id=test_student.id,
        title="Soon Attention Fee",
        total_amount=Decimal("500.00"),
        due_date=date.today() + timedelta(days=3),
        created_by=admin_user.id,
    )
    paid_fee = StudentFee(
        student_id=test_student.id,
        title="Recent Payment Fee",
        total_amount=Decimal("750.00"),
        due_date=date.today() + timedelta(days=30),
        created_by=admin_user.id,
    )
    test_db.add_all([overdue_fee, due_soon_fee, paid_fee])
    test_db.commit()
    test_db.refresh(paid_fee)
    test_db.add(
        Payment(
            student_fee_id=paid_fee.id,
            amount=Decimal("100.00"),
            payment_date=date.today(),
            payment_method="cash",
            recorded_by=admin_user.id,
        )
    )
    test_db.add(
        AttendanceSession(
            date=datetime.combine(date.today(), datetime.min.time()),
            course_id=test_course.id,
            batch_id=batch.id,
            semester_id=semester.id,
            subject_id=subject.id,
            session_name="Morning Lecture",
            created_by=admin_user.id,
        )
    )
    test_db.commit()

    response = client.get("/dashboard/attention", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    assert any(item["student_id"] == test_student.id for item in data["low_attendance_students"])
    assert any(item["title"] == "Overdue Attention Fee" for item in data["overdue_fees"])
    assert any(item["title"] == "Soon Attention Fee" for item in data["fees_due_soon"])
    assert any(item["subject_name"] == "Database Management Systems" for item in data["unmarked_attendance_sessions_today"])
    assert any(item["student_id"] == test_student.id for item in data["recently_admitted_students"])
    assert any(item["fee_title"] == "Recent Payment Fee" for item in data["recent_payments"])
