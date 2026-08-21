"""Unit tests for document security validation, magic byte header detection, zip-slip/zip-bomb protection, and SHA-256 hashing."""

import zipfile

import pytest

from finauditpro.infrastructure.documents.document_security import (
    DocumentSecurityError,
    calculate_sha256,
    detect_mime_type,
    sanitize_filename,
    validate_document_security,
    validate_zip_security,
)


def test_sanitize_filename() -> None:
    assert sanitize_filename("test_doc.pdf") == "test_doc.pdf"
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("C:\\Windows\\System32\\cmd.exe") == "cmd.exe"

    with pytest.raises(DocumentSecurityError):
        sanitize_filename("/\\")


def test_sha256_hashing(tmp_path) -> None:
    sample_file = tmp_path / "sample.txt"
    sample_file.write_bytes(b"FinAuditPro Statutory Audit Intelligence")

    digest = calculate_sha256(sample_file)
    assert len(digest) == 64
    assert digest == calculate_sha256(sample_file)  # Deterministic


def test_detect_mime_type_magic_bytes(tmp_path) -> None:
    pdf_file = tmp_path / "valid.pdf"
    pdf_file.write_bytes(b"%PDF-1.7 header content")
    assert detect_mime_type(pdf_file) == "application/pdf"

    png_file = tmp_path / "image.png"
    png_file.write_bytes(b"\x89PNG\r\n\x1a\nbytes")
    assert detect_mime_type(png_file) == "image/png"

    fake_pdf = tmp_path / "malicious.pdf"
    fake_pdf.write_bytes(b"NOT A REAL PDF FILE HEADER")

    # Mismatched magic byte check
    with pytest.raises(DocumentSecurityError):
        validate_document_security(fake_pdf)


def test_zip_slip_rejection(tmp_path) -> None:
    zip_path = tmp_path / "malicious_slip.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../evil.txt", b"malicious payload")

    with pytest.raises(DocumentSecurityError) as excinfo:
        validate_zip_security(zip_path)
    assert "Zip-slip" in str(excinfo.value)
