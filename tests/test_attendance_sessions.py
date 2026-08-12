from datetime import date, datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.attendance import AttendanceStatus
from app.models.attendance_session import AttendanceSession
from app.models.batch import Batch
from app.models.course import Course
from app.models.semester import Semester
from app.models.student import Student
from app.models.subject import Subject
from app.schemas.academic_year import AcademicYearCreate
from app.schemas.attendance_session import AttendanceBulkCreate, AttendanceSessionCreate
from app.schemas.batch import BatchCreate
from app.schemas.semester import SemesterCreate
from app.schemas.student import StudentCreate
from app.schemas.subject import SubjectCreate
from app.services import academic_year_service, batch_service, semester_service, subject_service


class TestAttendanceSessions:
    def test_create_session(
        self,
        client: TestClient,
        db: Session,
        admin_token: str,
        test_course: Course,
    ):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        semester = semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        batch = batch_service.create_batch(
            db,
            BatchCreate(
                name="MCA-2026-A",
                course_id=course.id,
                academic_year_id=year.id,
                capacity=60,
            ),
        )
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

        session_data = AttendanceSessionCreate(
            course_id=course.id,
            batch_id=batch.id,
            semester_id=semester.id,
            subject_id=subject.id,
            date=date.today().isoformat(),
            session_name="Morning Lecture",
        )

        response = client.post(
            "/attendance/sessions",
            json=session_data.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["session_name"] == "Morning Lecture"

    def test_create_session_future_date(
        self,
        client: TestClient,
        db: Session,
        admin_token: str,
        test_course: Course,
    ):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        semester = semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        batch = batch_service.create_batch(
            db,
            BatchCreate(
                name="MCA-2026-A",
                course_id=course.id,
                academic_year_id=year.id,
                capacity=60,
            ),
        )
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

        response = client.post(
            "/attendance/sessions",
            json={
                "course_id": course.id,
                "batch_id": batch.id,
                "semester_id": semester.id,
                "subject_id": subject.id,
                "date": "2099-12-31",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_get_sessions(self, client: TestClient, db: Session, admin_token: str):
        response = client.get(
            "/attendance/sessions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_bulk_create_attendance(
        self,
        client: TestClient,
        db: Session,
        admin_token: str,
        test_course: Course,
    ):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        semester = semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        batch = batch_service.create_batch(
            db,
            BatchCreate(
                name="MCA-2026-A",
                course_id=course.id,
                academic_year_id=year.id,
                capacity=60,
            ),
        )
        subject = subject_service.create_subject(
            db,
            SubjectCreate(
                course_id=course.id,
                semester_id=semester.id,
                code="CS101",
                name="Introduction to Programming",
            ),
        )
        student = Student(
            student_code="STU001",
            first_name="Test",
            last_name="Student",
            email="test@example.com",
            course_id=course.id,
            batch_id=batch.id,
        )
        db.add(student)
        db.commit()

        session = AttendanceSession(
            course_id=course.id,
            batch_id=batch.id,
            semester_id=semester.id,
            subject_id=subject.id,
            date=datetime.now(),
            created_by=1,
        )
        db.add(session)
        db.commit()

        response = client.post(
            f"/attendance/sessions/{session.id}/records/bulk",
            json={"records": [{"student_id": student.id, "status": "present"}]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_student_summary(self, db: Session, admin_token: str):
        student = db.query(Student).first()
        if not student:
            pytest.skip("No students available")

        response = client.get(
            f"/attendance/student/{student.id}/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_sessions" in data
        assert "attendance_percentage" in data

    def test_get_student_subject_summary(self, db: Session, admin_token: str):
        student = db.query(Student).first()
        if not student:
            pytest.skip("No students available")

        response = client.get(
            f"/attendance/student/{student.id}/subject-summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "subjects" in data

    def test_delete_session(
        self,
        client: TestClient,
        db: Session,
        admin_token: str,
        test_course: Course,
    ):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        semester = semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        batch = batch_service.create_batch(
            db,
            BatchCreate(
                name="MCA-2026-A",
                course_id=course.id,
                academic_year_id=year.id,
                capacity=60,
            ),
        )
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

        session = AttendanceSession(
            course_id=course.id,
            batch_id=batch.id,
            semester_id=semester.id,
            subject_id=subject.id,
            date=datetime.now(),
            created_by=1,
        )
        db.add(session)
        db.commit()

        response = client.delete(
            f"/attendance/sessions/{session.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
