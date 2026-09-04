"""Application-level column encryption using cryptography Fernet for sensitive data at rest."""

import base64
import os
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


def _get_app_data_dir() -> Path:
    """Return platform-aware application data directory."""
    from finauditpro.infrastructure.first_run import get_app_data_dir

    return get_app_data_dir()


def _get_key_file_path() -> Path:
    return _get_app_data_dir() / ".secret_key.key"


def _get_salt_file_path() -> Path:
    return _get_app_data_dir() / ".secret_salt.bin"


def _derive_kwk(passcode: str, salt: bytes) -> bytes:
    """Derive Key Wrapping Key (KWK) using memory-hard Scrypt."""
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=16384,
        r=8,
        p=1,
    )
    return kdf.derive(passcode.encode("utf-8"))


def _secure_write(path: Path, data: bytes) -> None:
    """Write bytes to path under strict owner-only (0600) permissions."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    # Ensure directory exists before opening file descriptor
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


def initialize_wrapped_dek(passcode: str) -> None:
    """Generate a random Data Encryption Key (DEK), wrap it with the passcode-derived KWK, and write to disk."""
    global _CIPHER
    salt_path = _get_salt_file_path()
    key_path = _get_key_file_path()

    # Generate a cryptographically secure random DEK (base64 urlsafe encoded)
    dek_bytes = base64.urlsafe_b64encode(os.urandom(32))

    # Generate a cryptographically secure random salt
    salt = os.urandom(16)
    _secure_write(salt_path, salt)

    # Derive KWK and wrap the DEK
    kwk = _derive_kwk(passcode, salt)
    kwk_fernet = Fernet(base64.urlsafe_b64encode(kwk))
    wrapped_dek = kwk_fernet.encrypt(dek_bytes)

    # Save wrapped DEK under strict permissions
    _secure_write(key_path, wrapped_dek)

    # Initialize session cipher in memory
    _CIPHER = Fernet(dek_bytes)


def rotate_passcode(old_passcode: str, new_passcode: str) -> None:
    """Unwrap the active DEK using the old passcode and re-wrap it with a new passcode, rotating the salt."""
    global _CIPHER
    salt_path = _get_salt_file_path()
    key_path = _get_key_file_path()

    if not salt_path.exists() or not key_path.exists():
        raise ValueError("Encryption has not been initialized on this system.")

    old_salt = salt_path.read_bytes()
    wrapped_dek = key_path.read_bytes()

    # 1. Unwrap DEK using old passcode
    old_kwk = _derive_kwk(old_passcode, old_salt)
    old_kwk_fernet = Fernet(base64.urlsafe_b64encode(old_kwk))
    try:
        dek_bytes = old_kwk_fernet.decrypt(wrapped_dek)
    except Exception as ex:
        raise ValueError("Invalid current passcode. Failed to unwrap key.") from ex

    # 2. Generate a new salt for salt rotation
    new_salt = os.urandom(16)
    new_kwk = _derive_kwk(new_passcode, new_salt)
    new_kwk_fernet = Fernet(base64.urlsafe_b64encode(new_kwk))

    # 3. Re-wrap DEK using new KWK
    new_wrapped_dek = new_kwk_fernet.encrypt(dek_bytes)

    # 4. Save new wrapped DEK and rotated salt
    _secure_write(salt_path, new_salt)
    _secure_write(key_path, new_wrapped_dek)

    # 5. Invalidate and reload active memory cipher
    _CIPHER = Fernet(dek_bytes)


def initialize_session_cipher(passcode: str) -> None:
    """Derive KWK from the passcode, decrypt the wrapped DEK, and load it into active memory.
    If a legacy 44-byte key is detected, it is securely wrapped and migrated under the new passcode.
    """
    global _CIPHER
    salt_path = _get_salt_file_path()
    key_path = _get_key_file_path()

    if not key_path.exists():
        raise ValueError("Encryption has not been initialized on this system.")

    wrapped_dek = key_path.read_bytes()

    # Detect and migrate legacy raw key (44 bytes base64)
    if len(wrapped_dek) == 44:
        try:
            legacy_dek = wrapped_dek
            Fernet(legacy_dek)

            # Generate fresh salt and write securely
            salt = os.urandom(16)
            _secure_write(salt_path, salt)

            # Derive KWK and wrap the legacy key
            kwk = _derive_kwk(passcode, salt)
            kwk_fernet = Fernet(base64.urlsafe_b64encode(kwk))
            new_wrapped_dek = kwk_fernet.encrypt(legacy_dek)

            # Overwrite with wrapped key securely
            _secure_write(key_path, new_wrapped_dek)

            # Set active memory cipher
            _CIPHER = Fernet(legacy_dek)
            return
        except Exception as ex:
            raise ValueError("Corrupt legacy key. Failed to migrate.") from ex

    if not salt_path.exists():
        raise ValueError("Missing cryptographic salt file.")

    salt = salt_path.read_bytes()

    # Derive KWK and decrypt DEK
    kwk = _derive_kwk(passcode, salt)
    kwk_fernet = Fernet(base64.urlsafe_b64encode(kwk))

    try:
        dek_bytes = kwk_fernet.decrypt(wrapped_dek)
    except Exception as ex:
        raise ValueError("Invalid passcode. Failed to decrypt Data Encryption Key.") from ex

    # Load decrypted DEK into memory
    _CIPHER = Fernet(dek_bytes)


def get_fernet_cipher() -> Fernet:
    """Return active session cipher, falling back to legacy fallback auto-initialization for unit tests."""
    global _CIPHER
    if _CIPHER is not None:
        return _CIPHER

    key_path = _get_key_file_path()
    salt_path = _get_salt_file_path()

    if key_path.exists() and salt_path.exists():
        wrapped_dek = key_path.read_bytes()
        # Fallback support for legacy raw Fernet keys
        if len(wrapped_dek) == 44:
            try:
                _CIPHER = Fernet(wrapped_dek)
                return _CIPHER
            except Exception:
                pass

        try:
            initialize_session_cipher("FinAuditPro-Local-Column-Secret-Key")
            if _CIPHER is not None:
                return _CIPHER
        except Exception:
            raise ValueError(
                "Access Denied: The Data Encryption Key is locked and requires user authorization."
            ) from None
    else:
        # Legacy/testing auto-initialization
        initialize_wrapped_dek("FinAuditPro-Local-Column-Secret-Key")

    if _CIPHER is None:
        raise RuntimeError("Failed to initialize cryptographic cipher.")
    return _CIPHER


_CIPHER: Fernet | None = None


def encrypt_sensitive_string(text: str | None) -> str | None:
    """Encrypt sensitive text column using active session cipher."""
    if not text:
        return text
    global _CIPHER
    if _CIPHER is None:
        _CIPHER = get_fernet_cipher()
    return _CIPHER.encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt_sensitive_string(cipher_text: str | None) -> str | None:
    """Decrypt sensitive text column using active session cipher. Fallback to raw string if unencrypted."""
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
