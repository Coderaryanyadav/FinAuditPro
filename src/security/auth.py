"""
Authentication, Session Token, & Password Security Manager for FinAuditPro.
Provides PBKDF2/Argon2 password hashing, cryptographic session tokens, auto-logout timers, and password reset handling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import os
import secrets
from typing import Dict, Optional, Any

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


class PasswordHasher:
    """Provides secure password hashing using PBKDF2-HMAC-SHA256 with salt."""

    ITERATIONS = 100000

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash plain text password with randomly generated 16-byte salt."""
        salt = os.urandom(16)
        hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, cls.ITERATIONS)
        return f"{salt.hex()}${hash_bytes.hex()}"

    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        """Verify plain text password against stored salt$hash string."""
        try:
            salt_hex, hash_hex = stored_hash.split("$")
            salt = bytes.fromhex(salt_hex)
            computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, cls.ITERATIONS)
            return computed_hash.hex() == hash_hex
        except Exception:
            return False


class AuthManager:
    """Manages session tokens, login authentication, and auto-logout timers."""

    def __init__(self, session_timeout_minutes: int = 60):
        self.session_timeout_minutes = session_timeout_minutes
        self.active_sessions: Dict[str, SessionToken] = {}

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
        return token

    def validate_session(self, token_str: str) -> Optional[SessionToken]:
        """Validates session token and handles auto-logout if expired."""
        token = self.active_sessions.get(token_str)
        if not token:
            return None

        if token.is_expired():
            del self.active_sessions[token_str]
            return None

        # Extend session expiry if active and not remember-me
        if not token.is_remember_me:
            token.expires_at = datetime.utcnow() + timedelta(minutes=self.session_timeout_minutes)

        return token

    def revoke_session(self, token_str: str) -> bool:
        """Logout user and revoke session token."""
        if token_str in self.active_sessions:
            del self.active_sessions[token_str]
            return True
        return False
