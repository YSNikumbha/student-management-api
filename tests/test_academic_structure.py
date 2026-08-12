import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.dependencies.auth import require_admin
from app.models.academic_year import AcademicYear
from app.models.batch import Batch
from app.models.course import Course
from app.models.semester import Semester
from app.models.student import Student
from app.models.subject import Subject
from app.schemas.academic_year import AcademicYearCreate
from app.schemas.batch import BatchCreate
from app.schemas.semester import SemesterCreate
from app.schemas.subject import SubjectCreate
from app.services import academic_year_service, batch_service, semester_service, subject_service


class TestAcademicYears:
    def test_create_academic_year(self, client, db: Session, admin_token: str):
        year_data = AcademicYearCreate(
            name="2026-27",
            start_date="2026-06-01",
            end_date="2027-05-31",
        )
        response = client.post(
            "/academic-years",
            json=year_data.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "2026-27"
        assert data["is_active"] is True

    def test_create_duplicate_academic_year(self, client, db: Session, admin_token: str):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2025-26", start_date="2025-06-01", end_date="2026-05-31")
        )
        db.commit()

        response = client.post(
            "/academic-years",
            json={"name": "2025-26", "start_date": "2025-06-01", "end_date": "2026-05-31"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_invalid_date_range(self, client, db: Session, admin_token: str):
        response = client.post(
            "/academic-years",
            json={"name": "Invalid", "start_date": "2027-05-31", "end_date": "2026-06-01"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_get_academic_years(self, client, db: Session, admin_token: str):
        academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2025-26", start_date="2025-06-01", end_date="2026-05-31")
        )
        db.commit()

        response = client.get(
            "/academic-years",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) >= 1

    def test_delete_academic_year_with_semesters(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        db.commit()

        course = test_course
        semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        db.commit()

        response = client.delete(
            f"/academic-years/{year.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestSemesters:
    def test_create_semester(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        db.commit()

        response = client.post(
            "/semesters",
            json={"academic_year_id": year.id, "course_id": course.id, "number": 1, "name": "Semester 1"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["number"] == 1
        assert data["name"] == "Semester 1"

    def test_create_duplicate_semester(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        db.commit()

        response = client.post(
            "/semesters",
            json={"academic_year_id": year.id, "course_id": course.id, "number": 1, "name": "Semester 1"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_semester_invalid_number(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        db.commit()

        response = client.post(
            "/semesters",
            json={"academic_year_id": year.id, "course_id": course.id, "number": 0, "name": "Semester 1"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestSubjects:
    def test_create_subject(self, client, db: Session, admin_token: str, test_course: Course):
        course = test_course
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        semester = semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        db.commit()

        response = client.post(
            "/subjects",
            json={"course_id": course.id, "semester_id": semester.id, "code": "CS101", "name": "Introduction to Programming"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["code"] == "CS101"

    def test_create_subject_code_uppercase(self, client, db: Session, admin_token: str, test_course: Course):
        course = test_course
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        semester = semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        db.commit()

        response = client.post(
            "/subjects",
            json={"course_id": course.id, "semester_id": semester.id, "code": "cs101", "name": "Introduction to Programming"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["code"] == "CS101"

    def test_create_subject_short_name(self, client, db: Session, admin_token: str, test_course: Course):
        course = test_course
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        semester = semester_service.create_semester(
            db,
            SemesterCreate(
                academic_year_id=year.id,
                course_id=course.id,
                number=1,
                name="Semester 1",
            ),
        )
        db.commit()

        response = client.post(
            "/subjects",
            json={"course_id": course.id, "semester_id": semester.id, "code": "CS101", "name": "AB"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestBatches:
    def test_create_batch(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        db.commit()

        response = client.post(
            "/batches",
            json={"name": "MCA-2026-A", "course_id": course.id, "academic_year_id": year.id, "capacity": 60},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "MCA-2026-A"

    def test_create_batch_invalid_capacity(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        db.commit()

        response = client.post(
            "/batches",
            json={"name": "MCA-2026-A", "course_id": course.id, "academic_year_id": year.id, "capacity": 0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_delete_batch_with_students(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        batch = batch_service.create_batch(
            db,
            BatchCreate(
                name="MCA-2026-A",
                course_id=course.id,
                academic_year_id=year.id,
                capacity=60,
            ),
        )
        db.commit()

        student = Student(
            student_code="STU001",
            first_name="Test",
            last_name="Student",
            email="test@example.com",
            batch_id=batch.id,
        )
        db.add(student)
        db.commit()

        response = client.delete(
            f"/batches/{batch.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestStudentAcademicAssignment:
    def test_assign_student_to_batch(self, client, db: Session, admin_token: str, test_course: Course):
        year = academic_year_service.create_academic_year(
            db, AcademicYearCreate(name="2026-27", start_date="2026-06-01", end_date="2027-05-31")
        )
        course = test_course
        batch = batch_service.create_batch(
            db,
            BatchCreate(
                name="MCA-2026-A",
                course_id=course.id,
                academic_year_id=year.id,
                capacity=60,
            ),
        )
        db.commit()

        response = client.post(
            "/students",
            json={
                "student_code": "STU001",
                "first_name": "Test",
                "last_name": "Student",
                "email": "test@example.com",
                "batch_id": batch.id,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["batch_id"] == batch.id


class TestRolePermissions:
    def test_staff_can_read_academic_years(self, client, db: Session, staff_token: str):
        response = client.get(
            "/academic-years",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_staff_cannot_create_academic_year(self, client, db: Session, staff_token: str):
        response = client.post(
            "/academic-years",
            json={"name": "2026-27", "start_date": "2026-06-01", "end_date": "2027-05-31"},
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_cannot_delete_semester(self, client, db: Session, staff_token: str, test_course: Course):
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
        db.commit()

        response = client.delete(
            f"/semesters/{semester.id}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN