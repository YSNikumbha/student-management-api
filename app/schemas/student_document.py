from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.student_document import StudentDocumentType


class StudentDocumentResponse(BaseModel):
    id: int
    student_id: int
    document_type: StudentDocumentType
    original_filename: str
    content_type: str
    file_size: int
    uploaded_by: int
    uploaded_by_name: str | None = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
