from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.academic_performance import Assessment, StudentResult
from app.models.batch import Batch
from app.models.student import Student
from app.models.subject import Subject
from app.schemas.academic_performance import AssessmentCreate, AssessmentUpdate, StudentResultCreate


def percentage_to_gpa(percentage: float) -> float:
    if percentage >= 90:
        return 4.0
    if percentage >= 80:
        return 3.7
    if percentage >= 70:
        return 3.3
    if percentage >= 60:
        return 3.0
    if percentage >= 50:
        return 2.0
    if percentage >= 40:
        return 1.0
    return 0.0


def percentage_to_grade(percentage: float) -> str:
    if percentage >= 90:
        return "A+"
    if percentage >= 80:
        return "A"
    if percentage >= 70:
        return "B+"
    if percentage >= 60:
        return "B"
    if percentage >= 50:
        return "C"
    if percentage >= 40:
        return "D"
    return "F"


def get_assessment(db: Session, assessment_id: int) -> Assessment | None:
    return db.get(Assessment, assessment_id)


def get_assessments(db: Session) -> list[Assessment]:
    return list(
        db.execute(
            select(Assessment).order_by(Assessment.date.desc(), Assessment.id.desc())
        ).scalars().all()
    )


def create_assessment(db: Session, data: AssessmentCreate) -> Assessment:
    assessment = Assessment(**data.model_dump())
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def update_assessment(db: Session, assessment: Assessment, data: AssessmentUpdate) -> Assessment:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assessment, field, value)
    assessment.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(assessment)
    return assessment


def upsert_result(
    db: Session,
    *,
    assessment: Assessment,
    data: StudentResultCreate,
) -> StudentResult:
    if data.marks_obtained > assessment.max_marks:
        raise ValueError("Marks obtained cannot exceed assessment max marks")
    percentage = float((data.marks_obtained / assessment.max_marks) * Decimal("100"))
    grade = percentage_to_grade(percentage)
    result = db.execute(
        select(StudentResult).where(
            StudentResult.assessment_id == assessment.id,
            StudentResult.student_id == data.student_id,
        )
    ).scalar_one_or_none()
    if result is None:
        result = StudentResult(
            assessment_id=assessment.id,
            student_id=data.student_id,
            marks_obtained=data.marks_obtained,
            grade=grade,
            remarks=data.remarks,
        )
        db.add(result)
    else:
        result.marks_obtained = data.marks_obtained
        result.grade = grade
        result.remarks = data.remarks
        result.updated_at = datetime.now(UTC)
    return result


def bulk_upsert_results(
    db: Session,
    *,
    assessment: Assessment,
    results: list[StudentResultCreate],
) -> list[StudentResult]:
    saved = [upsert_result(db, assessment=assessment, data=result) for result in results]
    db.commit()
    for result in saved:
        db.refresh(result)
    return saved


def get_student_academic_summary(db: Session, student_id: int) -> dict[str, float | int | str]:
    rows = db.execute(
        select(StudentResult, Assessment)
        .join(Assessment, StudentResult.assessment_id == Assessment.id)
        .where(StudentResult.student_id == student_id)
    ).all()
    return _summary_from_rows(student_id, rows)


def get_student_gpa_map(db: Session, student_ids: list[int] | None = None) -> dict[int, dict[str, float | int | str]]:
    statement = select(StudentResult, Assessment).join(Assessment, StudentResult.assessment_id == Assessment.id)
    if student_ids is not None:
        if not student_ids:
            return {}
        statement = statement.where(StudentResult.student_id.in_(student_ids))
    rows_by_student: dict[int, list[tuple[StudentResult, Assessment]]] = {}
    for result, assessment in db.execute(statement).all():
        rows_by_student.setdefault(result.student_id, []).append((result, assessment))
    return {
        student_id: _summary_from_rows(student_id, rows)
        for student_id, rows in rows_by_student.items()
    }


def _summary_from_rows(
    student_id: int,
    rows: list[tuple[StudentResult, Assessment]],
) -> dict[str, float | int | str]:
    weighted_points = Decimal("0.00")
    max_points = Decimal("0.00")
    for result, assessment in rows:
        weight = assessment.weight_percentage or Decimal("1.00")
        weighted_points += result.marks_obtained * weight
        max_points += assessment.max_marks * weight

    percentage = float((weighted_points / max_points) * Decimal("100")) if max_points else 0.0
    gpa = percentage_to_gpa(percentage)
    return {
        "student_id": student_id,
        "percentage": round(percentage, 2),
        "gpa": gpa,
        "grade": percentage_to_grade(percentage),
        "assessments_count": len(rows),
    }


def get_academic_report(db: Session) -> dict:
    students = list(db.execute(select(Student).options(selectinload(Student.batch))).scalars().all())
    gpa_map = get_student_gpa_map(db, [student.id for student in students])
    summaries = [gpa_map.get(student.id, _summary_from_rows(student.id, [])) for student in students]
    gpas = [float(summary["gpa"]) for summary in summaries]
    percentages = [float(summary["percentage"]) for summary in summaries]
    avg_gpa = round(mean(gpas), 2) if gpas else 0.0
    top_gpa = round(max(gpas), 2) if gpas else 0.0
    pass_rate = round((sum(1 for gpa in gpas if gpa >= 1.0) / len(gpas)) * 100, 2) if gpas else 0.0
    honor_roll = sum(1 for gpa in gpas if gpa >= 3.7)

    subject_rows = db.execute(
        select(
            Subject.id,
            Subject.name,
            func.avg((StudentResult.marks_obtained / Assessment.max_marks) * 100),
            func.max((StudentResult.marks_obtained / Assessment.max_marks) * 100),
            func.min((StudentResult.marks_obtained / Assessment.max_marks) * 100),
        )
        .join(Assessment, Assessment.subject_id == Subject.id)
        .join(StudentResult, StudentResult.assessment_id == Assessment.id)
        .group_by(Subject.id, Subject.name)
    ).all()
    subject_performance = [
        {
            "subject": name,
            "avg": round(float(avg or 0), 2),
            "highest": round(float(highest or 0), 2),
            "lowest": round(float(lowest or 0), 2),
        }
        for _subject_id, name, avg, highest, lowest in subject_rows
    ]

    bands = [
        ("3.5-4.0", lambda gpa: gpa >= 3.5),
        ("3.0-3.49", lambda gpa: 3.0 <= gpa < 3.5),
        ("2.0-2.99", lambda gpa: 2.0 <= gpa < 3.0),
        ("1.0-1.99", lambda gpa: 1.0 <= gpa < 2.0),
        ("<1.0", lambda gpa: gpa < 1.0),
    ]
    gpa_distribution = [
        {"range": label, "count": sum(1 for gpa in gpas if predicate(gpa))}
        for label, predicate in bands
    ]

    batch_groups: dict[int | None, list[float]] = {}
    batch_names = {batch.id: batch.name for batch in db.execute(select(Batch)).scalars().all()}
    for student, summary in zip(students, summaries, strict=False):
        batch_groups.setdefault(student.batch_id, []).append(float(summary["gpa"]))
    class_average_gpa = [
        {
            "class": batch_names.get(batch_id, "Unassigned"),
            "avgGpa": round(mean(values), 2) if values else 0.0,
        }
        for batch_id, values in batch_groups.items()
    ]

    ranked = sorted(
        [
            {
                "student_id": student.id,
                "student_name": f"{student.first_name} {student.last_name}",
                "student_code": student.student_code,
                "class_name": student.batch.name if student.batch else None,
                "gpa": float(gpa_map.get(student.id, _summary_from_rows(student.id, []))["gpa"]),
                "percentage": float(gpa_map.get(student.id, _summary_from_rows(student.id, []))["percentage"]),
            }
            for student in students
        ],
        key=lambda item: item["gpa"],
        reverse=True,
    )

    return {
        "summary": {
            "avg_school_gpa": avg_gpa,
            "top_gpa": top_gpa,
            "pass_rate": pass_rate,
            "honor_roll": honor_roll,
            "avg_percentage": round(mean(percentages), 2) if percentages else 0.0,
        },
        "subject_performance": subject_performance,
        "subject_radar": [{"subject": item["subject"], "score": item["avg"]} for item in subject_performance],
        "gpa_distribution": gpa_distribution,
        "class_average_gpa": class_average_gpa,
        "top_students": ranked[:10],
        "needs_attention": list(reversed(ranked))[:10],
    }
