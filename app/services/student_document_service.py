from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.student_document import StudentDocument, StudentDocumentType

MAX_DOCUMENT_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
CONTENT_TYPES_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


class DocumentValidationError(ValueError):
    def __init__(self, detail: str, status_code: int = 422) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class StoredDocumentFile:
    original_filename: str
    stored_filename: str
    content_type: str
    file_size: int
    path: Path


class LocalStudentDocumentStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or get_upload_root()

    def save(self, upload: UploadFile, *, student_id: int) -> StoredDocumentFile:
        original_filename = sanitize_filename(upload.filename or "document")
        extension = Path(original_filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise DocumentValidationError("Only PDF, JPG, JPEG, and PNG files are allowed")

        content = upload.file.read(MAX_DOCUMENT_SIZE + 1)
        upload.file.seek(0)
        if len(content) > MAX_DOCUMENT_SIZE:
            raise DocumentValidationError("Document file is too large", status_code=413)

        if not content:
            raise DocumentValidationError("Document file cannot be empty")

        content_type = detect_content_type(content, extension)
        if content_type is None:
            raise DocumentValidationError("File content does not match an allowed document type")

        student_dir = self.root / f"student_{student_id}"
        student_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4().hex}{extension}"
        storage_key = f"student_{student_id}/{stored_name}"
        target_path = student_dir / stored_name
        target_path.write_bytes(content)

        return StoredDocumentFile(
            original_filename=original_filename,
            stored_filename=storage_key,
            content_type=content_type,
            file_size=len(content),
            path=target_path,
        )

    def path_for(self, stored_filename: str) -> Path:
        storage_path = Path(stored_filename)
        if storage_path.is_absolute() or ".." in storage_path.parts:
            raise DocumentValidationError("Stored document path is invalid")
        return self.root / storage_path

    def delete(self, stored_filename: str) -> None:
        try:
            path = self.path_for(stored_filename)
        except DocumentValidationError:
            return
        if path.exists() and path.is_file():
            path.unlink()


def get_upload_root() -> Path:
    return Path(os.environ.get("STUDENT_DOCUMENT_UPLOAD_DIR", "uploads/student_documents")).resolve()


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    name = name.strip("._")
    if not name:
        return "document"
    return name[:255]


def detect_content_type(content: bytes, extension: str) -> str | None:
    if extension == ".pdf" and content.startswith(b"%PDF"):
        return CONTENT_TYPES_BY_EXTENSION[extension]
    if extension == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"):
        return CONTENT_TYPES_BY_EXTENSION[extension]
    if extension in {".jpg", ".jpeg"} and content.startswith(b"\xff\xd8\xff"):
        return CONTENT_TYPES_BY_EXTENSION[extension]
    return None


def get_document_by_id(
    db: Session,
    *,
    student_id: int,
    document_id: int,
) -> StudentDocument | None:
    statement = (
        select(StudentDocument)
        .options(selectinload(StudentDocument.uploader))
        .where(
            StudentDocument.id == document_id,
            StudentDocument.student_id == student_id,
        )
    )
    return db.execute(statement).scalar_one_or_none()


def get_student_documents(db: Session, student_id: int) -> list[StudentDocument]:
    statement = (
        select(StudentDocument)
        .options(selectinload(StudentDocument.uploader))
        .where(StudentDocument.student_id == student_id)
        .order_by(StudentDocument.uploaded_at.desc(), StudentDocument.id.desc())
    )
    return list(db.execute(statement).scalars().all())


def create_student_document(
    db: Session,
    *,
    student_id: int,
    document_type: StudentDocumentType,
    upload: UploadFile,
    uploaded_by: int,
    storage: LocalStudentDocumentStorage | None = None,
) -> StudentDocument:
    storage = storage or LocalStudentDocumentStorage()
    stored_file = storage.save(upload, student_id=student_id)
    document = StudentDocument(
        student_id=student_id,
        document_type=document_type.value,
        original_filename=stored_file.original_filename,
        stored_filename=stored_file.stored_filename,
        content_type=stored_file.content_type,
        file_size=stored_file.file_size,
        uploaded_by=uploaded_by,
    )
    db.add(document)
    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        storage.delete(stored_file.stored_filename)
        raise
    return get_document_by_id(db, student_id=student_id, document_id=document.id) or document


def delete_student_document(
    db: Session,
    document: StudentDocument,
    *,
    storage: LocalStudentDocumentStorage | None = None,
) -> None:
    storage = storage or LocalStudentDocumentStorage()
    stored_filename = document.stored_filename
    db.delete(document)
    db.commit()
    storage.delete(stored_filename)


def build_document_response(document: StudentDocument) -> dict:
    return {
        "id": document.id,
        "student_id": document.student_id,
        "document_type": document.document_type,
        "original_filename": document.original_filename,
        "content_type": document.content_type,
        "file_size": document.file_size,
        "uploaded_by": document.uploaded_by,
        "uploaded_by_name": document.uploader.name if document.uploader else None,
        "uploaded_at": document.uploaded_at,
    }
