"""Application-level column encryption using cryptography Fernet for sensitive data at rest."""

import base64
import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _get_app_data_dir() -> Path:
    """Return platform-aware application data directory (mirrors database.py logic)."""
    app_name = "FinAuditPro"
    if sys.platform == "darwin":
        data_dir = Path.home() / "Library" / "Application Support" / app_name
    elif sys.platform == "win32":
        app_data = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        data_dir = Path(app_data) / app_name
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        data_dir = Path(xdg_data) / app_name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _get_key_file_path() -> Path:
    return _get_app_data_dir() / ".secret_key.key"


def _get_salt_file_path() -> Path:
    return _get_app_data_dir() / ".secret_salt.bin"


def get_fernet_cipher() -> Fernet:
    """Load or generate machine-derived Fernet encryption key with persisted salt."""
    key_path = _get_key_file_path()
    salt_path = _get_salt_file_path()

    if key_path.exists():
        key_bytes = key_path.read_bytes()
    else:
        # Generate salt & derive key; persist both for recoverability
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        raw_key = kdf.derive(b"FinAuditPro-Local-Column-Secret-Key")
        key_bytes = base64.urlsafe_b64encode(raw_key)
        key_path.write_bytes(key_bytes)
        salt_path.write_bytes(salt)

    return Fernet(key_bytes)


_CIPHER: Fernet | None = None


def encrypt_sensitive_string(text: str | None) -> str | None:
    """Encrypt sensitive text column using Fernet."""
    if not text:
        return text
    global _CIPHER
    if _CIPHER is None:
        _CIPHER = get_fernet_cipher()
    return _CIPHER.encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt_sensitive_string(cipher_text: str | None) -> str | None:
    """Decrypt sensitive text column using Fernet. Fallback to raw string if unencrypted."""
    if not cipher_text:
        return cipher_text
    global _CIPHER
    if _CIPHER is None:
        _CIPHER = get_fernet_cipher()
    try:
        return _CIPHER.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        # Fallback if plaintext or key rotated
        return cipher_text
