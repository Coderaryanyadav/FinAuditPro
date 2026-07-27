"""
Authentication, Session Token, & Password Security Manager for FinAuditPro.
Provides PBKDF2/Argon2 password hashing, cryptographic session tokens, auto-logout timers, and password reset handling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import os
import secrets
import json
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class SessionToken:
    token_str: str
    user_id: int
    user_email: str
    role: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=8))
    is_remember_me: bool = False

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_str": self.token_str,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_remember_me": self.is_remember_me,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionToken":
        return cls(
            token_str=data["token_str"],
            user_id=data["user_id"],
            user_email=data["user_email"],
            role=data["role"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else datetime.utcnow(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if isinstance(data.get("expires_at"), str) else datetime.utcnow(),
            is_remember_me=data.get("is_remember_me", False),
        )


from core.config import config


class PasswordHasher:
    """Provides secure password hashing using PBKDF2-HMAC-SHA256 with salt and versioning."""

    ITERATIONS = config.pbkdf2_iterations

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash plain text password with randomly generated 16-byte salt and version prefix."""
        salt = os.urandom(16)
        hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, cls.ITERATIONS)
        return f"pbkdf2${cls.ITERATIONS}${salt.hex()}${hash_bytes.hex()}"

    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        """Verify plain text password against stored hash string (supports legacy salt$hash and pbkdf2$iter$salt$hash)."""
        try:
            parts = stored_hash.split("$")
            if len(parts) == 4 and parts[0] == "pbkdf2":
                _, iter_str, salt_hex, hash_hex = parts
                iterations = int(iter_str)
            elif len(parts) == 2:
                # Legacy unversioned hash format (100,000 iterations)
                salt_hex, hash_hex = parts
                iterations = 100000
            else:
                return False

            salt = bytes.fromhex(salt_hex)
            computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return secrets.compare_digest(computed_hash.hex(), hash_hex)
        except (ValueError, RuntimeError, AttributeError):
            return False

    @classmethod
    def needs_rehash(cls, stored_hash: str) -> bool:
        """Check if stored hash needs upgrading to current iteration count or version format."""
        try:
            parts = stored_hash.split("$")
            if len(parts) == 4 and parts[0] == "pbkdf2":
                return int(parts[1]) < cls.ITERATIONS
            return True  # Legacy format or invalid structure requires rehash
        except (ValueError, AttributeError):
            return True


class AuthManager:
    """Manages session tokens, login authentication, encrypted session persistence, and auto-logout timers."""

    def __init__(self, session_timeout_minutes: Optional[int] = None, storage_path: Optional[str] = None):
        self.session_timeout_minutes = session_timeout_minutes if session_timeout_minutes is not None else config.session_timeout_minutes
        if storage_path:
            self.storage_path = storage_path
        else:
            self.storage_path = os.path.join(config.data_dir, ".active_sessions.dat")

        self.active_sessions: Dict[str, SessionToken] = {}
        self._load_sessions()

    def _save_sessions(self) -> None:
        """Persists encrypted active sessions to disk."""
        try:
            from security.crypto import AESCryptoEngine
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            serialized = {
                t_str: tok.to_dict() for t_str, tok in self.active_sessions.items() if not tok.is_expired()
            }
            raw_bytes = json.dumps(serialized).encode("utf-8")
            engine = AESCryptoEngine()
            encrypted_data = engine.encrypt_bytes(raw_bytes)
            with open(self.storage_path, "wb") as f:
                f.write(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to persist active sessions: {e}")

    def _load_sessions(self) -> None:
        """Loads and decrypts active sessions from disk, discarding expired or tampered data."""
        if not os.path.exists(self.storage_path):
            return

        try:
            from security.crypto import AESCryptoEngine
            with open(self.storage_path, "rb") as f:
                encrypted_data = f.read()

            if not encrypted_data:
                return

            engine = AESCryptoEngine()
            decrypted_bytes = engine.decrypt_bytes(encrypted_data)
            data = json.loads(decrypted_bytes.decode("utf-8"))

            for token_str, token_dict in data.items():
                token = SessionToken.from_dict(token_dict)
                if not token.is_expired():
                    self.active_sessions[token.token_str] = token

            logger.info(f"Loaded {len(self.active_sessions)} active session(s) from persistent storage.")
        except Exception as e:
            logger.warning(f"Could not load active sessions from storage (possible tampering or corrupt file): {e}")
            self.active_sessions.clear()

    def create_session(self, user_id: int, user_email: str, role: str, is_remember_me: bool = False) -> SessionToken:
        """Generates a secure 32-byte cryptographic session token."""
        token_str = secrets.token_hex(32)
        expiry_hours = 720 if is_remember_me else (self.session_timeout_minutes / 60.0)
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

        token = SessionToken(
            token_str=token_str,
            user_id=user_id,
            user_email=user_email,
            role=role,
            expires_at=expires_at,
            is_remember_me=is_remember_me
        )
        self.active_sessions[token_str] = token
        self._save_sessions()
        return token

    def validate_session(self, token_str: str) -> Optional[SessionToken]:
        """Validates session token and handles auto-logout if expired."""
        token = self.active_sessions.get(token_str)
        if not token:
            return None

        if token.is_expired():
            del self.active_sessions[token_str]
            self._save_sessions()
            return None

        # Extend session expiry if active and not remember-me
        if not token.is_remember_me:
            token.expires_at = datetime.utcnow() + timedelta(minutes=self.session_timeout_minutes)
            self._save_sessions()

        return token

    def revoke_session(self, token_str: str) -> bool:
        """Logout user and revoke session token."""
        if token_str in self.active_sessions:
            del self.active_sessions[token_str]
            self._save_sessions()
            return True
        return False
