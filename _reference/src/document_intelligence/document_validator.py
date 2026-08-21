"""
Document Validation Module for FinAuditPro.
Validates file integrity, extension whitelist, max file size, password protection, and corrupt files.
"""

import os
from core.exceptions import ValidationError

class DocumentValidationError(ValidationError):
    """Raised when an uploaded audit document fails validation checks."""
    pass

class DocumentValidator:
    """Enforces strict document format, size, and security constraints."""

    ALLOWED_EXTENSIONS = {
        ".pdf", ".xlsx", ".xls", ".csv",
        ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
        ".docx", ".txt", ".json", ".xml"
    }

    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB max file size

    MAGIC_BYTES = {
        ".pdf": b"%PDF",
        ".png": b"\x89PNG\r\n\x1a\n",
        ".jpg": b"\xff\xd8\xff",
        ".jpeg": b"\xff\xd8\xff",
        ".xlsx": b"PK\x03\x04",
        ".docx": b"PK\x03\x04",
    }

    @classmethod
    def validate_file(cls, file_path: str) -> bool:
        """
        Validates file existence, size, extension, magic header signature, and integrity.
        Raises DocumentValidationError if invalid.
        """
        if not os.path.exists(file_path):
            raise DocumentValidationError(f"File path does not exist: {file_path}")

        if not os.path.isfile(file_path):
            raise DocumentValidationError(f"Target path is not a file: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise DocumentValidationError(
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(cls.ALLOWED_EXTENSIONS))}"
            )

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise DocumentValidationError("File is empty (0 bytes).")

        if file_size > cls.MAX_FILE_SIZE_BYTES:
            raise DocumentValidationError(
                f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum limit of 100MB."
            )

        # Magic Header Content Sniffing Check
        if ext in cls.MAGIC_BYTES:
            expected_prefix = cls.MAGIC_BYTES[ext]
            try:
                with open(file_path, "rb") as f:
                    header = f.read(len(expected_prefix))
                    if header != expected_prefix:
                        raise DocumentValidationError(
                            f"File signature mismatch for '{ext}'. File header does not match expected format."
                        )
            except (OSError, IOError) as e:
                raise DocumentValidationError(f"Unable to read file headers: {e}")

        # PDF Password & Corruption Check
        if ext == ".pdf":
            cls._validate_pdf(file_path)

        return True

    @classmethod
    def _validate_pdf(cls, file_path: str) -> None:
        """Check if PDF is encrypted, password protected, or corrupted."""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            if reader.is_encrypted:
                raise DocumentValidationError("PDF is password-protected or encrypted. Please decrypt before uploading.")
            if len(reader.pages) == 0:
                raise DocumentValidationError("PDF has no readable pages.")
        except DocumentValidationError:
            raise
        except (OSError, ValueError) as e:
            raise DocumentValidationError(f"Corrupt or unreadable PDF file: {e}")
