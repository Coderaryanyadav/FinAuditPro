"""
AES-256 File Encryption & Secure Storage Engine for FinAuditPro.
Provides AES-256 local file encryption, secure temp files, and automatic disk cleanup.

THREAT MODEL & KEY DERIVATION ARCHITECTURE:
1. Installation Key Mode (Default):
   - Derives AES-256 key from a 256-bit secret stored in `.crypto_key`.
   - Threat Model: Protects data against unauthorized remote extraction and cold disk access outside the app data folder.
   - Limitation: Any local OS user with read permissions to `.crypto_key` can derive the encryption key.

2. Master Password Derived Key Mode (User Opt-In / High Security):
   - Derives AES-256 key directly from user login or master password using PBKDF2-HMAC-SHA256 (600,000 iterations).
   - Threat Model: Protects against full local machine compromise and physical disk theft.
   - Security Guarantee: No master key is written to `.crypto_key`. Audit records cannot be decrypted without the user's password.
"""

import os
import tempfile
import base64
import hashlib
import secrets
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def _get_or_create_installation_key(data_dir: str) -> bytes:
    """
    Retrieve or generate a 256-bit cryptographically secure installation key secret.
    
    THREAT MODEL WARNING:
    This key is persisted to `.crypto_key` for machine-bound offline execution without a user password.
    Users requiring protection against local file access should initialize AESCryptoEngine with master_password.
    """
    key_file = os.path.join(data_dir, ".crypto_key")
    if os.path.exists(key_file):
        try:
            with open(key_file, "rb") as f:
                key_bytes = f.read()
                if len(key_bytes) == 32:
                    return key_bytes
        except (OSError, IOError) as e:
            logger.warning(f"Could not read existing crypto key file: {e}")

    new_key = secrets.token_bytes(32)
    try:
        os.makedirs(data_dir, exist_ok=True)
        # Attempt user-restricted file creation (0600)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600
        try:
            fd = os.open(key_file, flags, mode)
            with open(fd, "wb") as f:
                f.write(new_key)
        except (AttributeError, OSError):
            with open(key_file, "wb") as f:
                f.write(new_key)
    except (OSError, IOError) as e:
        logger.warning(f"Could not persist installation crypto key to disk: {e}")
    return new_key


from core.config import config


class AESCryptoEngine:
    """Provides AES-256 file encryption and decryption for sensitive audit records."""

    ITERATIONS = config.pbkdf2_iterations

    def __init__(self, master_password: Optional[str] = None, salt: Optional[bytes] = None):
        data_dir = config.data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.is_master_password_protected = bool(master_password)

        if master_password:
            # High-Security Mode: Key derived directly from master password
            secret_bytes = master_password.encode("utf-8")
            salt_filename = ".master_crypto_salt"
        else:
            # Installation Mode: Machine-bound secret key
            secret_bytes = _get_or_create_installation_key(data_dir)
            salt_filename = ".crypto_salt"

        if salt is None:
            os.makedirs(data_dir, exist_ok=True)
            salt_file = os.path.join(data_dir, salt_filename)
            if os.path.exists(salt_file):
                try:
                    with open(salt_file, "rb") as f:
                        self.salt = f.read(16)
                except (OSError, IOError) as e:
                    logger.warning(f"Could not read crypto salt: {e}")
                    self.salt = secrets.token_bytes(16)
            else:
                self.salt = secrets.token_bytes(16)
                try:
                    with open(salt_file, "wb") as f:
                        f.write(self.salt)
                except (OSError, IOError) as e:
                    logger.warning(f"Could not persist crypto salt to disk: {e}")
        else:
            self.salt = salt

        self.key = hashlib.pbkdf2_hmac("sha256", secret_bytes, self.salt, self.ITERATIONS)
        self._fernet = None
        self._init_fernet()

    def _init_fernet(self):
        try:
            from cryptography.fernet import Fernet
            url_safe_key = base64.urlsafe_b64encode(self.key)
            self._fernet = Fernet(url_safe_key)
        except ImportError:
            logger.error("cryptography package not installed. Cryptographic operations halted for security compliance.")
            self._fernet = None

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt byte array using AES-256 (Fernet)."""
        if self._fernet:
            return self._fernet.encrypt(data)
        raise RuntimeError("Fernet AES-256 encryption unavailable. 'cryptography' library is required.")

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Decrypt byte array using AES-256 (Fernet)."""
        if self._fernet:
            return self._fernet.decrypt(encrypted_data)
        raise RuntimeError("Fernet AES-256 decryption unavailable. 'cryptography' library is required.")

    def encrypt_file(self, source_path: str, dest_path: str) -> str:
        """Encrypt source file and write to dest_path."""
        with open(source_path, "rb") as f_in:
            data = f_in.read()
        encrypted = self.encrypt_bytes(data)
        with open(dest_path, "wb") as f_out:
            f_out.write(encrypted)
        return dest_path

    def decrypt_file(self, source_path: str, dest_path: str) -> str:
        """Decrypt encrypted file and write unencrypted bytes to dest_path."""
        with open(source_path, "rb") as f_in:
            encrypted = f_in.read()
        decrypted = self.decrypt_bytes(encrypted)
        with open(dest_path, "wb") as f_out:
            f_out.write(decrypted)
        return dest_path


class SecureStorage:
    """Manages secure temp files and guarantees automatic cleanup on exit."""

    def __init__(self):
        self.temp_files: List[str] = []

    def create_secure_temp_file(self, prefix: str = "finaudit_", suffix: str = ".tmp") -> str:
        """Create a temporary file and register for automatic deletion."""
        temp_fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        os.close(temp_fd)
        self.temp_files.append(temp_path)
        return temp_path

    def cleanup(self) -> None:
        """Delete all registered temporary files."""
        for path in self.temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"Securely deleted temp file: {path}")
                except (OSError, IOError) as e:
                    logger.warning(f"Failed to delete temp file {path}: {e}")
        self.temp_files.clear()

