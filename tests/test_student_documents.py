from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


PDF_BYTES = b"%PDF-1.4\n% test document\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


def test_valid_document_upload_list_download_and_delete(
    client: TestClient,
    admin_headers: dict,
    test_student,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDENT_DOCUMENT_UPLOAD_DIR", str(tmp_path))

    upload_response = client.post(
        f"/students/{test_student.id}/documents",
        headers=admin_headers,
        data={"document_type": "identity_proof"},
        files={"file": ("identity proof.pdf", PDF_BYTES, "application/pdf")},
    )
    assert upload_response.status_code == 201
    document = upload_response.json()
    assert document["document_type"] == "identity_proof"
    assert document["original_filename"] == "identity_proof.pdf"
    assert document["content_type"] == "application/pdf"
    assert document["file_size"] == len(PDF_BYTES)
    assert document["uploaded_by_name"] == "Test Admin"

    list_response = client.get(
        f"/students/{test_student.id}/documents",
        headers=admin_headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    view_response = client.get(
        f"/students/{test_student.id}/documents/{document['id']}/view",
        headers=admin_headers,
    )
    assert view_response.status_code == 200
    assert view_response.headers["content-type"].startswith("application/pdf")
    assert view_response.content.startswith(b"%PDF")

    download_response = client.get(
        f"/students/{test_student.id}/documents/{document['id']}/download",
        headers=admin_headers,
    )
    assert download_response.status_code == 200
    assert "attachment" in download_response.headers["content-disposition"]
    assert download_response.content.startswith(b"%PDF")

    delete_response = client.delete(
        f"/students/{test_student.id}/documents/{document['id']}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 204

    missing_download = client.get(
        f"/students/{test_student.id}/documents/{document['id']}/download",
        headers=admin_headers,
    )
    assert missing_download.status_code == 404


def test_document_upload_rejects_invalid_extension(
    client: TestClient,
    admin_headers: dict,
    test_student,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDENT_DOCUMENT_UPLOAD_DIR", str(tmp_path))

    response = client.post(
        f"/students/{test_student.id}/documents",
        headers=admin_headers,
        data={"document_type": "other"},
        files={"file": ("script.exe", b"MZ executable", "application/octet-stream")},
    )
    assert response.status_code == 422
    assert "allowed" in response.json()["detail"].lower()


def test_document_upload_rejects_mismatched_content(
    client: TestClient,
    admin_headers: dict,
    test_student,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDENT_DOCUMENT_UPLOAD_DIR", str(tmp_path))

    response = client.post(
        f"/students/{test_student.id}/documents",
        headers=admin_headers,
        data={"document_type": "marksheet"},
        files={"file": ("marksheet.pdf", b"<script>alert(1)</script>", "application/pdf")},
    )
    assert response.status_code == 422
    assert "content" in response.json()["detail"].lower()


def test_document_upload_rejects_large_file(
    client: TestClient,
    admin_headers: dict,
    test_student,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDENT_DOCUMENT_UPLOAD_DIR", str(tmp_path))
    large_pdf = b"%PDF" + (b"x" * (5 * 1024 * 1024))

    response = client.post(
        f"/students/{test_student.id}/documents",
        headers=admin_headers,
        data={"document_type": "certificate"},
        files={"file": ("large.pdf", large_pdf, "application/pdf")},
    )
    assert response.status_code == 413


def test_document_upload_missing_student(
    client: TestClient,
    admin_headers: dict,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDENT_DOCUMENT_UPLOAD_DIR", str(tmp_path))

    response = client.post(
        "/students/99999/documents",
        headers=admin_headers,
        data={"document_type": "profile_photo"},
        files={"file": ("photo.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 404


def test_document_authorization(
    client: TestClient,
    staff_headers: dict,
    test_student,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDENT_DOCUMENT_UPLOAD_DIR", str(tmp_path))

    unauthenticated_list = client.get(f"/students/{test_student.id}/documents")
    assert unauthenticated_list.status_code == 401

    staff_upload = client.post(
        f"/students/{test_student.id}/documents",
        headers=staff_headers,
        data={"document_type": "other"},
        files={"file": ("note.pdf", PDF_BYTES, "application/pdf")},
    )
    assert staff_upload.status_code == 403

    staff_list = client.get(
        f"/students/{test_student.id}/documents",
        headers=staff_headers,
    )
    assert staff_list.status_code == 200


def test_document_delete_requires_admin(
    client: TestClient,
    admin_headers: dict,
    staff_headers: dict,
    test_student,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDENT_DOCUMENT_UPLOAD_DIR", str(tmp_path))

    upload_response = client.post(
        f"/students/{test_student.id}/documents",
        headers=admin_headers,
        data={"document_type": "admission_document"},
        files={"file": ("admission.pdf", PDF_BYTES, "application/pdf")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]

    delete_response = client.delete(
        f"/students/{test_student.id}/documents/{document_id}",
        headers=staff_headers,
    )
    assert delete_response.status_code == 403
