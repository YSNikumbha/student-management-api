import os
from datetime import date, datetime
from decimal import Decimal
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.security import hash_password
from app.database.base import Base
from app.database.database import get_db
from app.main import app
from app.models.academic_year import AcademicYear
from app.models.academic_performance import Assessment, StudentResult
from app.models.audit_log import AuditLog
from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession
from app.models.batch import Batch
from app.models.course import Course
from app.models.fee_category import FeeCategory
from app.models.fee_installment import FeeInstallment
from app.models.fee_structure import FeeStructure
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.semester import Semester
from app.models.student import Student
from app.models.student_document import StudentDocument
from app.models.student_fee import StudentFee
from app.models.subject import Subject
from app.models.system_setting import NotificationPreference, SystemSetting
from app.models.user import User


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Override settings for tests
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine for the entire test session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # Enable foreign keys for SQLite
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    
    # Start a savepoint for rollback
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
    # Rollback everything after the test
    session.close()
    transaction.rollback()
    connection.close()


# Alias for tests that use 'db' instead of 'test_db'
@pytest.fixture(scope="function")
def db(test_db) -> Session:
    """Alias for test_db to maintain compatibility with tests using 'db'."""
    return test_db


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(test_db) -> User:
    """Create an admin user for testing."""
    user = User(
        name="Test Admin",
        email="admin@test.com",
        hashed_password=hash_password("TestPassword123!"),
        role="admin",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def staff_user(test_db) -> User:
    """Create a staff user for testing."""
    user = User(
        name="Test Staff",
        email="staff@test.com",
        hashed_password=hash_password("TestPassword123!"),
        role="staff",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def inactive_user(test_db) -> User:
    """Create an inactive user for testing."""
    user = User(
        name="Inactive User",
        email="inactive@test.com",
        hashed_password=hash_password("TestPassword123!"),
        role="staff",
        is_active=False,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_token(client, admin_user) -> str:
    """Get JWT token for admin user."""
    response = client.post(
        "/auth/login",
        json={
            "email": admin_user.email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def staff_token(client, staff_user) -> str:
    """Get JWT token for staff user."""
    response = client.post(
        "/auth/login",
        json={
            "email": staff_user.email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict[str, str]:
    """Get headers with admin authorization."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def staff_headers(staff_token: str) -> dict[str, str]:
    """Get headers with staff authorization."""
    return {"Authorization": f"Bearer {staff_token}"}


@pytest.fixture(scope="function")
def test_course(test_db) -> Course:
    """Create a test course."""
    course = Course(
        code="TEST101",
        name="Test Course",
        description="A test course",
        duration_months=6,
        is_active=True,
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)
    return course


@pytest.fixture(scope="function")
def test_course_with_students(test_db, test_course) -> Course:
    """Create a course with students for testing."""
    students = [
        Student(
            student_code=f"STU00{i}",
            first_name=f"Student{i}",
            last_name=f"Last{i}",
            email=f"student{i}@test.com",
            course_id=test_course.id,
            status="active",
        )
        for i in range(1, 4)
    ]
    # Fix names to not contain numbers to pass validation
    for i, student in enumerate(students):
        student.first_name = f"Student{chr(64+i)}"  # StudentA, StudentB, StudentC
        student.last_name = f"Last{chr(64+i)}"      # LastA, LastB, LastC
    test_db.add_all(students)
    test_db.commit()
    return test_course


@pytest.fixture(scope="function")
def test_student(test_db, test_course) -> Student:
    """Create a test student."""
    student = Student(
        student_code="STU001",
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        course_id=test_course.id,
        status="active",
    )
    test_db.add(student)
    test_db.commit()
    test_db.refresh(student)
    return student


@pytest.fixture(scope="function")
def test_fee(test_db, test_student, admin_user) -> StudentFee:
    """Create a test fee."""
    fee = StudentFee(
        student_id=test_student.id,
        title="Test Fee",
        description="A test fee",
        total_amount=Decimal("60000.00"),
        due_date=date(2026, 12, 31),
        created_by=admin_user.id,
    )
    test_db.add(fee)
    test_db.commit()
    test_db.refresh(fee)
    return fee


@pytest.fixture(scope="function")
def attendance_session_context(test_db, test_course, admin_user) -> dict[str, object]:
    """Create a complete attendance-session graph with one marked student."""
    academic_year = AcademicYear(
        name="Attendance Test 2026-27",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    test_db.add(academic_year)
    test_db.flush()

    semester = Semester(
        academic_year_id=academic_year.id,
        course_id=test_course.id,
        number=1,
        name="Attendance Test Semester",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 12, 31),
        is_active=True,
    )
    test_db.add(semester)
    test_db.flush()

    batch = Batch(
        name="ATT-2026-A",
        course_id=test_course.id,
        academic_year_id=academic_year.id,
        semester_id=semester.id,
        capacity=60,
        is_active=True,
    )
    subject = Subject(
        course_id=test_course.id,
        semester_id=semester.id,
        code="ATT101",
        name="Attendance Test Subject",
        is_active=True,
    )
    test_db.add_all([batch, subject])
    test_db.flush()

    student = Student(
        student_code="ATT-STU-001",
        first_name="Aarav",
        last_name="Sharma",
        email="attendance.student@test.com",
        course_id=test_course.id,
        academic_year_id=academic_year.id,
        semester_id=semester.id,
        batch_id=batch.id,
        status="active",
    )
    test_db.add(student)
    test_db.flush()

    session_date = datetime(2026, 8, 12, 9, 0, 0)
    attendance_session = AttendanceSession(
        course_id=test_course.id,
        batch_id=batch.id,
        semester_id=semester.id,
        subject_id=subject.id,
        date=session_date,
        session_name="Attendance Test Lecture",
        created_by=admin_user.id,
    )
    test_db.add(attendance_session)
    test_db.flush()

    attendance = Attendance(
        attendance_session_id=attendance_session.id,
        student_id=student.id,
        date=session_date.date(),
        status="present",
        marked_by=admin_user.id,
    )
    test_db.add(attendance)
    test_db.commit()

    for entity in (academic_year, semester, batch, subject, student, attendance_session, attendance):
        test_db.refresh(entity)

    return {
        "academic_year": academic_year,
        "semester": semester,
        "batch": batch,
        "subject": subject,
        "student": student,
        "session": attendance_session,
        "attendance": attendance,
    }
