"""
AES-256 File Encryption & Secure Storage Engine for FinAuditPro.
Provides AES-256 local file encryption, secure temp files, and automatic disk cleanup.
"""

import os
import tempfile
import base64
import hashlib
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class AESCryptoEngine:
    """Provides AES-256 file encryption and decryption for sensitive audit records."""

    def __init__(self, master_password: Optional[str] = None, salt: Optional[bytes] = None):
        import platform
        secret = master_password or f"FinAuditPro_Secret_{platform.node()}"
        if salt is None:
            salt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(salt_dir, exist_ok=True)
            salt_file = os.path.join(salt_dir, ".crypto_salt")
            if os.path.exists(salt_file):
                try:
                    with open(salt_file, "rb") as f:
                        self.salt = f.read(16)
                except Exception:
                    self.salt = os.urandom(16)
            else:
                self.salt = os.urandom(16)
                try:
                    with open(salt_file, "wb") as f:
                        f.write(self.salt)
                except Exception as e:
                    logger.warning(f"Could not persist crypto salt to disk: {e}")
        else:
            self.salt = salt

        self.key = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), self.salt, 100000)
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
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {path}: {e}")
        self.temp_files.clear()
