from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.student_document import StudentDocument, StudentDocumentType
from app.models.user import User
from app.schemas.student_document import StudentDocumentResponse
from app.services import student_document_service, student_service
from app.services.student_document_service import DocumentValidationError, LocalStudentDocumentStorage

router = APIRouter(
    prefix="/students",
    tags=["Student Documents"],
)


def _ensure_student_exists(db: Session, student_id: int) -> None:
    if student_service.get_student_by_id(db, student_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )


def _get_document_or_404(
    db: Session,
    *,
    student_id: int,
    document_id: int,
) -> StudentDocument:
    document = student_document_service.get_document_by_id(
        db,
        student_id=student_id,
        document_id=document_id,
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


def _file_response(
    document: StudentDocument,
    *,
    disposition: str,
) -> FileResponse:
    storage = LocalStudentDocumentStorage()
    try:
        path = storage.path_for(document.stored_filename)
    except DocumentValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found",
        ) from error

    if not path.exists() or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found",
        )

    return FileResponse(
        Path(path),
        media_type=document.content_type,
        filename=document.original_filename,
        content_disposition_type=disposition,
    )


@router.post(
    "/{student_id}/documents",
    response_model=StudentDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_student_document(
    student_id: int,
    document_type: StudentDocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    _ensure_student_exists(db, student_id)

    try:
        document = student_document_service.create_student_document(
            db,
            student_id=student_id,
            document_type=document_type,
            upload=file,
            uploaded_by=current_user.id,
        )
    except DocumentValidationError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error

    return student_document_service.build_document_response(document)


@router.get(
    "/{student_id}/documents",
    response_model=list[StudentDocumentResponse],
)
def list_student_documents(
    student_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[dict]:
    _ensure_student_exists(db, student_id)
    documents = student_document_service.get_student_documents(db, student_id)
    return [
        student_document_service.build_document_response(document)
        for document in documents
    ]


@router.get("/{student_id}/documents/{document_id}/view")
def view_student_document(
    student_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FileResponse:
    document = _get_document_or_404(
        db,
        student_id=student_id,
        document_id=document_id,
    )
    return _file_response(document, disposition="inline")


@router.get("/{student_id}/documents/{document_id}/download")
def download_student_document(
    student_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FileResponse:
    document = _get_document_or_404(
        db,
        student_id=student_id,
        document_id=document_id,
    )
    return _file_response(document, disposition="attachment")


@router.delete(
    "/{student_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student_document(
    student_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> Response:
    document = _get_document_or_404(
        db,
        student_id=student_id,
        document_id=document_id,
    )
    student_document_service.delete_student_document(db, document)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
