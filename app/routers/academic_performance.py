from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.academic_performance import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentUpdate,
    BulkStudentResultRequest,
    StudentAcademicSummaryResponse,
    StudentResultResponse,
)
from app.services import academic_performance_service

router = APIRouter(
    prefix="/academic-performance",
    tags=["Academic Performance"],
)


@router.get("/assessments", response_model=list[AssessmentResponse])
def get_assessments(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return academic_performance_service.get_assessments(db)


@router.post(
    "/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    assessment_data: AssessmentCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return academic_performance_service.create_assessment(db, assessment_data)


@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
def update_assessment(
    assessment_id: int,
    assessment_data: AssessmentUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    assessment = academic_performance_service.get_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return academic_performance_service.update_assessment(db, assessment, assessment_data)


@router.post(
    "/assessments/{assessment_id}/results/bulk",
    response_model=list[StudentResultResponse],
)
def bulk_upsert_results(
    assessment_id: int,
    result_data: BulkStudentResultRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    assessment = academic_performance_service.get_assessment(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    try:
        return academic_performance_service.bulk_upsert_results(
            db,
            assessment=assessment,
            results=result_data.results,
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.get("/students/{student_id}/summary", response_model=StudentAcademicSummaryResponse)
def get_student_academic_summary(
    student_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return academic_performance_service.get_student_academic_summary(db, student_id)
