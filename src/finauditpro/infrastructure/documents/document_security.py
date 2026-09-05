"""Document security validation, magic byte checking, SHA-256 hashing, zip-slip/zip-bomb protection, and safe path resolution."""

import hashlib
import zipfile
from pathlib import Path

from finauditpro.domain.exceptions import DomainError

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_UNCOMPRESSED_ZIP_BYTES = 200 * 1024 * 1024  # 200 MB
MAX_ZIP_ENTRIES = 500
MAX_ZIP_COMPRESSION_RATIO = 100.0


class DocumentSecurityError(DomainError):
    """Raised when document security validation or integrity checks fail."""
    pass


def get_native_storage_dir() -> Path:
    """Return immutable native platform document storage directory."""
    from finauditpro.infrastructure.first_run import get_app_data_dir

    doc_dir = get_app_data_dir() / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


def calculate_sha256(file_path: Path | str) -> str:
    """Compute SHA-256 hex digest of a file in 64KB chunks."""
    path = Path(file_path)
    if not path.is_file():
        raise DocumentSecurityError(f"File not found: '{path}'")

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to prevent path traversal attacks across operating systems."""
    posix_path = str(filename).replace("\\", "/")
    pure_name = Path(posix_path).name
    cleaned = pure_name.lstrip("/\\.").strip()
    if not cleaned:
        raise DocumentSecurityError(f"Invalid filename: '{filename}'")
    return cleaned


def detect_mime_type(file_path: Path | str) -> str:
    """Inspect file header magic bytes to determine mime type."""
    path = Path(file_path)
    if not path.is_file():
        return "application/octet-stream"

    with path.open("rb") as f:
        header = f.read(16)

    if header.startswith(b"%PDF"):
        return "application/pdf"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
        return "image/tiff"
    if header.startswith(b"PK\x03\x04"):
        ext = path.suffix.lower()
        if ext == ".xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if ext == ".docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return "application/zip"
    if path.suffix.lower() == ".csv":
        return "text/csv"
    if path.suffix.lower() in (".txt", ".log", ".md"):
        return "text/plain"

    return "application/octet-stream"


def validate_zip_security(path: Path) -> None:
    """Guard against zip-slip (path traversal) and zip-bomb decompression attacks."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            infolist = zf.infolist()
            if len(infolist) > MAX_ZIP_ENTRIES:
                raise DocumentSecurityError(
                    f"ZIP archive contains {len(infolist)} entries, exceeding security threshold of {MAX_ZIP_ENTRIES}."
                )

            total_uncompressed = 0
            total_compressed = 0
            for info in infolist:
                # Zip-Slip Path Traversal Protection
                member_name = info.filename.replace("\\", "/")
                if ".." in member_name or member_name.startswith("/") or ":" in member_name:
                    raise DocumentSecurityError(
                        f"Zip-slip path traversal attempt detected in archive entry: '{info.filename}'"
                    )

                total_uncompressed += info.file_size
                total_compressed += info.compress_size

            if total_uncompressed > MAX_UNCOMPRESSED_ZIP_BYTES:
                raise DocumentSecurityError(
                    f"ZIP uncompressed payload ({total_uncompressed / (1024 * 1024):.1f} MB) exceeds maximum allowed size of {MAX_UNCOMPRESSED_ZIP_BYTES / (1024 * 1024):.0f} MB."
                )

            if total_compressed > 0:
                ratio = total_uncompressed / total_compressed
                if ratio > MAX_ZIP_COMPRESSION_RATIO:
                    raise DocumentSecurityError(
                        f"ZIP compression ratio ({ratio:.1f}:1) indicates potential zip bomb."
                    )
    except zipfile.BadZipFile as ex:
        raise DocumentSecurityError(f"Corrupted or invalid ZIP/XLSX file: {ex}") from ex


def validate_document_security(
    file_path: Path | str, max_size_bytes: int = MAX_FILE_SIZE_BYTES
) -> str:
    """Perform fail-closed security verification on an incoming file.

    Inspects size, magic byte signatures, zip safety, and sanitizes filenames.
    Returns SHA-256 content hash on clean pass.
    """
    path = Path(file_path)
    if not path.is_file():
        raise DocumentSecurityError(f"File does not exist: '{path}'")

    file_size = path.stat().st_size
    if file_size == 0:
        raise DocumentSecurityError("Zero-byte file rejected.")
    if file_size > max_size_bytes:
        raise DocumentSecurityError(
            f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum limit of {max_size_bytes / (1024 * 1024):.0f} MB."
        )

    # Sanitize filename
    sanitize_filename(path.name)

    # Header Magic-Byte Verification
    mime_type = detect_mime_type(path)
    ext = path.suffix.lower()

    if ext == ".pdf" and mime_type != "application/pdf":
        raise DocumentSecurityError("File claims to be PDF (.pdf) but magic header does not match %PDF signature.")

    if ext in (".png", ".jpg", ".jpeg", ".tiff") and not mime_type.startswith("image/"):
        raise DocumentSecurityError(f"File extension '{ext}' does not match detected header mime type '{mime_type}'.")

    if mime_type in ("application/zip", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        validate_zip_security(path)

    return calculate_sha256(path)
