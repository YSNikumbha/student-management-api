from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.database import SessionLocal
from app.models.academic_performance import Assessment, StudentResult
from app.models.academic_year import AcademicYear
from app.models.attendance import Attendance
from app.models.attendance_session import AttendanceSession
from app.models.audit_log import AuditLog
from app.models.batch import Batch
from app.models.course import Course
from app.models.fee_category import FeeCategory
from app.models.fee_structure import FeeStructure
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.semester import Semester
from app.models.student import Student
from app.models.student_fee import StudentFee
from app.models.subject import Subject
from app.models.user import User
from app.services import academic_performance_service, role_permission_service


DEMO_EMAIL_DOMAIN = "example.com"
DEMO_PASSWORD = "DemoPass123"

FIRST_NAMES = [
    "Aarav", "Aditi", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Krish",
    "Meera", "Neha", "Pranav", "Riya", "Rohan", "Saanvi", "Vivaan", "Zoya",
    "Aditya", "Nisha", "Rahul", "Sneha", "Tanvi", "Yash", "Kiran", "Pooja",
]
LAST_NAMES = [
    "Sharma", "Patel", "Iyer", "Nair", "Reddy", "Kulkarni", "Mehta", "Joshi",
    "Menon", "Gupta", "Chatterjee", "Pillai", "Desai", "Bhat", "Verma", "Khan",
]


def get_or_create_user(db: Session, *, name: str, email: str, role: str) -> tuple[User, bool]:
    existing = db.execute(select(User).where(func.lower(User.email) == email.lower())).scalar_one_or_none()
    if existing:
        return existing, False
    user = User(
        name=name,
        email=email.lower(),
        hashed_password=hash_password(DEMO_PASSWORD),
        role=role,
        is_active=True,
    )
    role_permission_service.assign_role_to_user(db, user, role_name=role)
    db.add(user)
    db.flush()
    return user, True


def get_or_create(db: Session, model, lookup: dict, values: dict) -> tuple[object, bool]:
    statement = select(model)
    for field, value in lookup.items():
        statement = statement.where(getattr(model, field) == value)
    existing = db.execute(statement).scalar_one_or_none()
    if existing:
        return existing, False
    obj = model(**{**lookup, **values})
    db.add(obj)
    db.flush()
    return obj, True


def reset_demo_data(db: Session) -> dict[str, int]:
    counts: dict[str, int] = {}
    demo_student_ids = list(db.execute(select(Student.id).where(Student.student_code.like("DEMO%"))).scalars().all())
    demo_user_ids = list(db.execute(select(User.id).where(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}"))).scalars().all())
    demo_batch_ids = list(db.execute(select(Batch.id).where(Batch.name.like("%-2026-%"))).scalars().all())
    demo_subject_ids = list(db.execute(select(Subject.id).where(Subject.code.like("DEMO-%"))).scalars().all())
    demo_fee_ids = list(db.execute(select(StudentFee.id).where(StudentFee.invoice_number.like("DEMO-INV-%"))).scalars().all())
    demo_assessment_ids = list(db.execute(select(Assessment.id).where(Assessment.name.like("Demo %"))).scalars().all())

    statements = [
        ("audit_logs", delete(AuditLog).where(AuditLog.description.like("Demo %"))),
        ("notifications", delete(Notification).where(Notification.message.like("Demo %"))),
    ]
    if demo_fee_ids:
        statements.extend([
            ("payments", delete(Payment).where(Payment.student_fee_id.in_(demo_fee_ids))),
            ("student_fees", delete(StudentFee).where(StudentFee.id.in_(demo_fee_ids))),
        ])
    if demo_assessment_ids:
        statements.extend([
            ("student_results", delete(StudentResult).where(StudentResult.assessment_id.in_(demo_assessment_ids))),
            ("assessments", delete(Assessment).where(Assessment.id.in_(demo_assessment_ids))),
        ])
    if demo_student_ids:
        statements.extend([
            ("attendances", delete(Attendance).where(Attendance.student_id.in_(demo_student_ids))),
            ("students", delete(Student).where(Student.id.in_(demo_student_ids))),
        ])
    if demo_subject_ids:
        statements.append(("subjects", delete(Subject).where(Subject.id.in_(demo_subject_ids))))
    if demo_batch_ids:
        statements.extend([
            ("attendance_sessions", delete(AttendanceSession).where(AttendanceSession.batch_id.in_(demo_batch_ids))),
            ("batches", delete(Batch).where(Batch.id.in_(demo_batch_ids))),
        ])
    statements.extend([
        ("fee_structures", delete(FeeStructure).where(FeeStructure.name.like("Demo %"))),
        ("fee_categories", delete(FeeCategory).where(FeeCategory.name.in_(["Tuition", "Hostel", "Exam", "Library", "Lab"]))),
        ("semesters", delete(Semester).where(Semester.name.like("Demo Semester %"))),
        ("academic_years", delete(AcademicYear).where(AcademicYear.name.like("Demo AY %"))),
        ("courses", delete(Course).where(Course.code.in_(["MCA-DEMO", "BCA-DEMO"]))),
    ])
    if demo_user_ids:
        statements.append(("users", delete(User).where(User.id.in_(demo_user_ids), User.role != "admin")))

    for label, statement in statements:
        result = db.execute(statement)
        counts[label] = int(result.rowcount or 0)
    db.commit()
    return counts


def seed(
    db: Session,
    *,
    student_count: int = 56,
    attendance_days: int = 75,
) -> dict[str, dict[str, int]]:
    role_permission_service.ensure_default_roles_and_permissions(db)
    summary: dict[str, dict[str, int]] = {}

    def bump(group: str, inserted: bool) -> None:
        summary.setdefault(group, {"inserted": 0, "skipped": 0})
        summary[group]["inserted" if inserted else "skipped"] += 1

    admin, inserted = get_or_create_user(db, name="Demo Admin", email=f"demo.admin@{DEMO_EMAIL_DOMAIN}", role="admin")
    bump("users", inserted)
    teachers = []
    for index, name in enumerate(["Priya Nair", "Arvind Rao", "Megha Kulkarni"], start=1):
        user, inserted = get_or_create_user(db, name=name, email=f"demo.teacher{index}@{DEMO_EMAIL_DOMAIN}", role="teacher")
        teachers.append(user)
        bump("users", inserted)
    accountant, inserted = get_or_create_user(db, name="Neeraj Shah", email=f"demo.accountant@{DEMO_EMAIL_DOMAIN}", role="accountant")
    bump("users", inserted)

    courses = []
    for code, name, months in [("MCA-DEMO", "Master of Computer Applications", 24), ("BCA-DEMO", "Bachelor of Computer Applications", 36)]:
        course, inserted = get_or_create(db, Course, {"code": code}, {"name": name, "description": "Demo portfolio course", "duration_months": months, "is_active": True})
        courses.append(course)
        bump("courses", inserted)

    today = date.today()
    current_year = today.year if today.month >= 7 else today.year - 1
    academic_years = []
    for offset in [0, 1]:
        ay, inserted = get_or_create(
            db,
            AcademicYear,
            {"name": f"Demo AY {current_year + offset}-{str(current_year + offset + 1)[-2:]}"},
            {"start_date": date(current_year + offset, 7, 1), "end_date": date(current_year + offset + 1, 6, 30), "is_active": offset == 0},
        )
        academic_years.append(ay)
        bump("academic_years", inserted)

    semesters = []
    for course in courses:
        for number in range(1, 5):
            sem, inserted = get_or_create(
                db,
                Semester,
                {"academic_year_id": academic_years[0].id, "course_id": course.id, "number": number, "name": f"Demo Semester {number} {course.code}"},
                {"start_date": academic_years[0].start_date + timedelta(days=(number - 1) * 90), "end_date": academic_years[0].start_date + timedelta(days=number * 90 - 1), "is_active": number <= 2},
            )
            semesters.append(sem)
            bump("semesters", inserted)

    batches = []
    for course in courses:
        course_semesters = [sem for sem in semesters if sem.course_id == course.id]
        for section in ["A", "B", "C", "D"] if course.code == "MCA-DEMO" else ["A", "B", "C"]:
            batch, inserted = get_or_create(
                db,
                Batch,
                {"name": f"{course.code.split('-')[0]}-{current_year}-{section}"},
                {
                    "course_id": course.id,
                    "academic_year_id": academic_years[0].id,
                    "semester_id": course_semesters[0].id,
                    "class_teacher_id": teachers[len(batches) % len(teachers)].id,
                    "section": section,
                    "capacity": 60,
                    "room": f"Lab-{len(batches) + 101}",
                    "schedule": "Mon-Fri 09:00-15:30",
                    "is_active": True,
                },
            )
            batches.append(batch)
            bump("classes", inserted)

    subjects = []
    subject_names = [
        ("DS", "Data Structures"),
        ("DBMS", "Database Management Systems"),
        ("OS", "Operating Systems"),
        ("CN", "Computer Networks"),
        ("PY", "Python Programming"),
        ("JAVA", "Java Programming"),
        ("SE", "Software Engineering"),
        ("AI", "Artificial Intelligence"),
        ("WEB", "Web Technologies"),
        ("STAT", "Applied Statistics"),
    ]
    for index, (code, name) in enumerate(subject_names):
        course = courses[index % len(courses)]
        semester = next(sem for sem in semesters if sem.course_id == course.id)
        subject, inserted = get_or_create(
            db,
            Subject,
            {"code": f"DEMO-{code}", "course_id": course.id, "semester_id": semester.id},
            {"name": name, "description": "Demo subject", "credits": 4, "is_active": True},
        )
        subjects.append(subject)
        bump("subjects", inserted)

    students = []
    for index in range(1, student_count + 1):
        first_name = FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index - 1) % len(LAST_NAMES)]
        batch = batches[(index - 1) % len(batches)]
        student, inserted = get_or_create(
            db,
            Student,
            {"student_code": f"DEMO{index:03d}"},
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": f"demo.student{index:03d}@{DEMO_EMAIL_DOMAIN}",
                "phone": f"900000{index:04d}",
                "date_of_birth": date(2003 + (index % 5), (index % 12) + 1, min((index % 27) + 1, 28)),
                "gender": "female" if index % 3 == 0 else "male",
                "address": f"Demo Hostel Block {chr(65 + index % 4)}, Pune",
                "parent_name": f"{LAST_NAMES[index % len(LAST_NAMES)]} Parent",
                "parent_phone": f"911111{index:04d}",
                "blood_group": ["A+", "B+", "O+", "AB+"][index % 4],
                "course_id": batch.course_id,
                "academic_year_id": batch.academic_year_id,
                "semester_id": batch.semester_id,
                "batch_id": batch.id,
                "admission_date": academic_years[0].start_date + timedelta(days=index % 30),
                "status": "active",
            },
        )
        students.append(student)
        bump("students", inserted)

    start_attendance = today - timedelta(days=attendance_days - 1)
    for day_offset in range(0, attendance_days):
        attendance_date = start_attendance + timedelta(days=day_offset)
        if attendance_date.weekday() >= 5:
            continue
        for batch in batches:
            subject = next(subject for subject in subjects if subject.course_id == batch.course_id)
            session, inserted = get_or_create(
                db,
                AttendanceSession,
                {"batch_id": batch.id, "subject_id": subject.id, "date": datetime.combine(attendance_date, time(9, 30))},
                {
                    "course_id": batch.course_id,
                    "semester_id": batch.semester_id,
                    "session_name": "Demo Daily Attendance",
                    "created_by": teachers[0].id,
                },
            )
            bump("attendance_sessions", inserted)
            batch_students = [student for student in students if student.batch_id == batch.id]
            for student in batch_students:
                status_index = (student.id + day_offset) % 20
                att_status = "present"
                if status_index == 0:
                    att_status = "excused"
                elif status_index in {1, 2}:
                    att_status = "absent"
                elif status_index in {3, 4}:
                    att_status = "late"
                record, inserted = get_or_create(
                    db,
                    Attendance,
                    {"student_id": student.id, "date": attendance_date},
                    {"attendance_session_id": session.id, "status": att_status, "remarks": "Demo attendance", "marked_by": teachers[0].id},
                )
                bump("attendance", inserted)

    assessments = []
    assessment_dates = [today - timedelta(days=70), today - timedelta(days=40), today - timedelta(days=15)]
    for subject in subjects:
        semester = next(sem for sem in semesters if sem.id == subject.semester_id)
        for label, assessment_date in zip(["Mid Term", "Lab", "End Term"], assessment_dates, strict=True):
            assessment, inserted = get_or_create(
                db,
                Assessment,
                {"name": f"Demo {label} {subject.code}", "subject_id": subject.id},
                {
                    "semester_id": semester.id,
                    "academic_year_id": semester.academic_year_id,
                    "assessment_type": label,
                    "max_marks": Decimal("100.00"),
                    "weight_percentage": Decimal("1.00"),
                    "date": assessment_date,
                },
            )
            assessments.append(assessment)
            bump("assessments", inserted)
            for student in [item for item in students if item.course_id == subject.course_id]:
                raw = 48 + ((student.id * 7 + subject.id * 5 + len(label) * 3) % 50)
                result, inserted = get_or_create(
                    db,
                    StudentResult,
                    {"assessment_id": assessment.id, "student_id": student.id},
                    {"marks_obtained": Decimal(raw), "grade": academic_performance_service.percentage_to_grade(float(raw)), "remarks": "Demo result"},
                )
                bump("student_results", inserted)

    current_month_start = max(today.replace(day=1), academic_years[0].start_date)
    current_assessment_dates = [
        ("Current Month Quiz", current_month_start),
        ("Current Month Practical", today),
    ]
    for subject in subjects:
        semester = next(sem for sem in semesters if sem.id == subject.semester_id)
        for label, assessment_date in current_assessment_dates:
            assessment, inserted = get_or_create(
                db,
                Assessment,
                {"name": f"Demo {label} {today:%b %Y} {subject.code}", "subject_id": subject.id},
                {
                    "semester_id": semester.id,
                    "academic_year_id": semester.academic_year_id,
                    "assessment_type": label,
                    "max_marks": Decimal("100.00"),
                    "weight_percentage": Decimal("1.00"),
                    "date": assessment_date,
                },
            )
            bump("assessments", inserted)
            for student in [item for item in students if item.course_id == subject.course_id]:
                raw = 52 + ((student.id * 9 + subject.id * 4 + len(label)) % 44)
                result, inserted = get_or_create(
                    db,
                    StudentResult,
                    {"assessment_id": assessment.id, "student_id": student.id},
                    {
                        "marks_obtained": Decimal(raw),
                        "grade": academic_performance_service.percentage_to_grade(float(raw)),
                        "remarks": "Demo current-period result",
                    },
                )
                bump("student_results", inserted)

    categories = []
    for category_name in ["Tuition", "Hostel", "Exam", "Library", "Lab"]:
        category, inserted = get_or_create(db, FeeCategory, {"name": category_name}, {"description": "Demo fee category", "is_active": True})
        categories.append(category)
        bump("fee_categories", inserted)

    fee_structures = []
    for course in courses:
        for category in categories:
            amount = {"Tuition": "45000.00", "Hostel": "30000.00", "Exam": "3500.00", "Library": "2500.00", "Lab": "6000.00"}[category.name]
            structure, inserted = get_or_create(
                db,
                FeeStructure,
                {"name": f"Demo {course.code} {category.name}", "course_id": course.id, "academic_year_id": academic_years[0].id, "category_id": category.id},
                {"semester_id": None, "total_amount": Decimal(amount), "description": "Demo fee structure", "is_active": True},
            )
            fee_structures.append(structure)
            bump("fee_structures", inserted)

    for student in students:
        applicable = [structure for structure in fee_structures if structure.course_id == student.course_id]
        for index, structure in enumerate(applicable[:3]):
            due_date = today + timedelta(days=(index - 1) * 35 + (student.id % 10))
            fee, inserted = get_or_create(
                db,
                StudentFee,
                {"invoice_number": f"DEMO-INV-{student.student_code}-{index + 1}"},
                {
                    "student_id": student.id,
                    "fee_structure_id": structure.id,
                    "title": structure.name.replace("Demo ", ""),
                    "description": "Demo fee assignment",
                    "total_amount": structure.total_amount,
                    "due_date": due_date,
                    "created_by": accountant.id,
                },
            )
            bump("student_fees", inserted)
            payment_pattern = student.id % 4
            payment_amount = Decimal("0.00")
            if payment_pattern == 0:
                payment_amount = fee.total_amount
            elif payment_pattern == 1:
                payment_amount = (fee.total_amount / Decimal("2")).quantize(Decimal("0.01"))
            if payment_amount > 0:
                payment, inserted = get_or_create(
                    db,
                    Payment,
                    {"receipt_number": f"DEMO-RCPT-{student.student_code}-{index + 1}"},
                    {
                        "student_fee_id": fee.id,
                        "amount": payment_amount,
                        "payment_date": max(today - timedelta(days=20 - index), academic_years[0].start_date),
                        "payment_method": ["cash", "upi", "bank_transfer"][index % 3],
                        "reference_number": f"DEMO-PAY-{student.id}-{index}",
                        "notes": "Demo payment",
                        "recorded_by": accountant.id,
                    },
                )
                bump("payments", inserted)

        current_structure = applicable[0]
        current_fee, inserted = get_or_create(
            db,
            StudentFee,
            {"invoice_number": f"DEMO-INV-CUR-{student.student_code}-{today:%Y%m}"},
            {
                "student_id": student.id,
                "fee_structure_id": current_structure.id,
                "title": "Current Month Demo Fee",
                "description": "Demo fee assignment for active report filters",
                "total_amount": Decimal("8000.00"),
                "due_date": today,
                "created_by": accountant.id,
            },
        )
        bump("student_fees", inserted)
        current_payment_amount = Decimal("0.00")
        if student.id % 4 == 0:
            current_payment_amount = current_fee.total_amount
        elif student.id % 4 == 1:
            current_payment_amount = (current_fee.total_amount / Decimal("2")).quantize(Decimal("0.01"))
        if current_payment_amount > 0:
            payment, inserted = get_or_create(
                db,
                Payment,
                {"receipt_number": f"DEMO-RCPT-CUR-{student.student_code}-{today:%Y%m}"},
                {
                    "student_fee_id": current_fee.id,
                    "amount": current_payment_amount,
                    "payment_date": today,
                    "payment_method": ["cash", "upi", "bank_transfer"][student.id % 3],
                    "reference_number": f"DEMO-CUR-PAY-{student.id}-{today:%Y%m}",
                    "notes": "Demo current-period payment",
                    "recorded_by": accountant.id,
                },
            )
            bump("payments", inserted)

    for user in [admin, *teachers, accountant]:
        for index in range(2):
            notification, inserted = get_or_create(
                db,
                Notification,
                {"user_id": user.id, "title": f"Demo Notification {index + 1}", "message": f"Demo notification for {user.name} #{index + 1}"},
                {"type": "system", "is_read": index == 0},
            )
            bump("notifications", inserted)

    for action, entity_type in [("demo_seeded", "system"), ("demo_user_created", "user"), ("demo_report_viewed", "report")]:
        audit, inserted = get_or_create(
            db,
            AuditLog,
            {"action": action, "entity_type": entity_type, "description": f"Demo audit event: {action}"},
            {"user_id": admin.id, "entity_id": None, "metadata_json": {"demo": True}, "ip_address": "127.0.0.1"},
        )
        bump("audit_logs", inserted)

    db.commit()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed explicit demo data for local development.")
    parser.add_argument("--reset-demo", action="store_true", help="Delete only deterministic demo-tagged data before seeding.")
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.reset_demo:
            removed = reset_demo_data(db)
            print("Reset demo data:")
            for label, count in sorted(removed.items()):
                print(f"  {label}: {count}")
        summary = seed(db)

    print("Demo seed summary:")
    for label, counts in sorted(summary.items()):
        print(f"  {label}: inserted={counts['inserted']} skipped={counts['skipped']}")
    print(f"Demo password for seeded users: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
