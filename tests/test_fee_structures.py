from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.academic_year import AcademicYear
from app.models.batch import Batch
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User


PASSWORD = "TestPassword123!"


def _create_academic_setup(db: Session, course):
    year = AcademicYear(
        name="2026-2027",
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
        name="Semester 1",
        is_active=True,
    )
    db.add(semester)
    db.commit()
    db.refresh(semester)

    batch = Batch(
        name="FEE-2026-A",
        course_id=course.id,
        academic_year_id=year.id,
        semester_id=semester.id,
        is_active=True,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return year, semester, batch


def _create_batch_students(db: Session, course, year, semester, batch) -> list[Student]:
    students = [
        Student(
            student_code=f"FEE00{i}",
            first_name=f"Fee{i}",
            last_name="Student",
            email=f"fee{i}@test.com",
            course_id=course.id,
            academic_year_id=year.id,
            semester_id=semester.id,
            batch_id=batch.id,
            status="active",
        )
        for i in range(1, 3)
    ]
    db.add_all(students)
    db.commit()
    for student in students:
        db.refresh(student)
    return students


def _create_category(client: TestClient, admin_headers: dict) -> int:
    response = client.post(
        "/fees/categories",
        headers=admin_headers,
        json={"name": "Tuition Test", "description": "Tuition category"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_structure(
    client: TestClient,
    admin_headers: dict,
    course,
    year,
    semester,
    category_id: int,
) -> int:
    response = client.post(
        "/fees/structures",
        headers=admin_headers,
        json={
            "name": "MCA Semester 1 Tuition Fee",
            "course_id": course.id,
            "academic_year_id": year.id,
            "semester_id": semester.id,
            "category_id": category_id,
            "total_amount": "60000.00",
            "description": "Semester tuition",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _headers_for_role(client: TestClient, db: Session, role: str) -> dict[str, str]:
    user = User(
        name=f"Fee {role.title()}",
        email=f"fee.{role}@test.com",
        hashed_password=hash_password(PASSWORD),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    response = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_fee_category_and_structure_crud(
    client: TestClient,
    admin_headers: dict,
    test_db: Session,
    test_course,
) -> None:
    year, semester, _batch = _create_academic_setup(test_db, test_course)
    category_id = _create_category(client, admin_headers)
    structure_id = _create_structure(client, admin_headers, test_course, year, semester, category_id)

    list_response = client.get("/fees/structures", headers=admin_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total_items"] >= 1

    update_response = client.put(
        f"/fees/structures/{structure_id}",
        headers=admin_headers,
        json={"name": "Updated Tuition Fee", "is_active": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Tuition Fee"


def test_batch_assignment_skips_duplicates(
    client: TestClient,
    admin_headers: dict,
    test_db: Session,
    test_course,
) -> None:
    year, semester, batch = _create_academic_setup(test_db, test_course)
    _students = _create_batch_students(test_db, test_course, year, semester, batch)
    category_id = _create_category(client, admin_headers)
    structure_id = _create_structure(client, admin_headers, test_course, year, semester, category_id)

    payload = {"batch_id": batch.id, "due_date": "2026-08-31"}
    first_response = client.post(
        f"/fees/structures/{structure_id}/assign",
        headers=admin_headers,
        json=payload,
    )
    assert first_response.status_code == 201
    assert first_response.json()["created"] == 2
    assert first_response.json()["skipped"] == 0

    second_response = client.post(
        f"/fees/structures/{structure_id}/assign",
        headers=admin_headers,
        json=payload,
    )
    assert second_response.status_code == 201
    assert second_response.json()["created"] == 0
    assert second_response.json()["skipped"] == 2


def test_installments_sum_cannot_exceed_fee(
    client: TestClient,
    admin_headers: dict,
    test_fee,
) -> None:
    response = client.post(
        f"/fees/{test_fee.id}/installments",
        headers=admin_headers,
        json={
            "title": "Oversized",
            "amount": "999999.00",
            "due_date": "2026-08-31",
            "sequence_number": 1,
        },
    )
    assert response.status_code == 409


def test_payment_receipt_uniqueness_and_pdf(
    client: TestClient,
    admin_headers: dict,
    test_fee,
) -> None:
    payment_one = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "100.00",
            "payment_date": "2025-01-15",
            "payment_method": "cash",
        },
    )
    assert payment_one.status_code == 201
    payment_two = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "100.00",
            "payment_date": "2025-01-16",
            "payment_method": "upi",
        },
    )
    assert payment_two.status_code == 201

    receipt_one = payment_one.json()["receipt_number"]
    receipt_two = payment_two.json()["receipt_number"]
    assert receipt_one.startswith("RCPT-2025-")
    assert receipt_two.startswith("RCPT-2025-")
    assert receipt_one != receipt_two

    receipt_response = client.get(
        f"/payments/{payment_one.json()['id']}/receipt",
        headers=admin_headers,
    )
    assert receipt_response.status_code == 200
    assert receipt_response.json()["receipt_number"] == receipt_one

    pdf_response = client.get(
        f"/payments/{payment_one.json()['id']}/receipt/pdf",
        headers=admin_headers,
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF")


def test_payment_allocation_to_installment_rejects_overpayment(
    client: TestClient,
    admin_headers: dict,
    test_fee,
) -> None:
    installment = client.post(
        f"/fees/{test_fee.id}/installments",
        headers=admin_headers,
        json={
            "title": "First Installment",
            "amount": "500.00",
            "due_date": "2026-08-31",
            "sequence_number": 1,
        },
    )
    assert installment.status_code == 201

    response = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "600.00",
            "payment_date": "2025-01-15",
            "payment_method": "cash",
            "fee_installment_id": installment.json()["id"],
        },
    )
    assert response.status_code == 409


def test_financial_delete_restrictions(
    client: TestClient,
    admin_headers: dict,
    test_db: Session,
    test_course,
    test_fee,
) -> None:
    installment = client.post(
        f"/fees/{test_fee.id}/installments",
        headers=admin_headers,
        json={
            "title": "Restricted Installment",
            "amount": "500.00",
            "due_date": "2026-08-31",
            "sequence_number": 1,
        },
    )
    assert installment.status_code == 201
    payment = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "100.00",
            "payment_date": "2025-01-15",
            "payment_method": "cash",
            "fee_installment_id": installment.json()["id"],
        },
    )
    assert payment.status_code == 201

    delete_installment = client.delete(
        f"/fees/installments/{installment.json()['id']}",
        headers=admin_headers,
    )
    assert delete_installment.status_code == 409

    year, semester, batch = _create_academic_setup(test_db, test_course)
    _students = _create_batch_students(test_db, test_course, year, semester, batch)
    category_id = _create_category(client, admin_headers)
    structure_id = _create_structure(client, admin_headers, test_course, year, semester, category_id)
    assign_response = client.post(
        f"/fees/structures/{structure_id}/assign",
        headers=admin_headers,
        json={"batch_id": batch.id, "due_date": "2026-08-31"},
    )
    assert assign_response.status_code == 201

    delete_structure = client.delete(f"/fees/structures/{structure_id}", headers=admin_headers)
    assert delete_structure.status_code == 409


def test_fee_structure_permissions(
    client: TestClient,
    test_db: Session,
    test_course,
) -> None:
    year, semester, _batch = _create_academic_setup(test_db, test_course)
    teacher_headers = _headers_for_role(client, test_db, "teacher")
    category_response = client.post(
        "/fees/categories",
        headers=teacher_headers,
        json={"name": "Teacher Blocked"},
    )
    assert category_response.status_code == 403

    accountant_headers = _headers_for_role(client, test_db, "accountant")
    category_id = client.post(
        "/fees/categories",
        headers=accountant_headers,
        json={"name": "Accountant Category"},
    ).json()["id"]
    structure_response = client.post(
        "/fees/structures",
        headers=accountant_headers,
        json={
            "name": "Accountant Structure",
            "course_id": test_course.id,
            "academic_year_id": year.id,
            "semester_id": semester.id,
            "category_id": category_id,
            "total_amount": "1000.00",
        },
    )
    assert structure_response.status_code == 201
