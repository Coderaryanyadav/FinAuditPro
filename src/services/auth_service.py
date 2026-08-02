import time
from typing import Optional, Dict, Any
from core.exceptions import AuthenticationError, ValidationError
from database.repositories.user_repo import UserRepository
from database.models import User

from security.auth import PasswordHasher
from security.security_manager import SecurityManager

import json
import os

LOCKOUT_FILE = os.path.join("data", ".login_lockouts.json")


def _get_crypto():
    """Return an AESCryptoEngine instance for lockout file encryption."""
    try:
        from security.crypto import AESCryptoEngine
        return AESCryptoEngine()
    except Exception:
        return None


def _load_lockout_records() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(LOCKOUT_FILE):
        return {}
    try:
        with open(LOCKOUT_FILE, "rb") as f:
            encrypted = f.read()
        crypto = _get_crypto()
        if crypto and encrypted:
            decrypted = crypto.decrypt_bytes(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        # Fallback: legacy plain-text file (migrate on next save)
        with open(LOCKOUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_lockout_records(records: Dict[str, Dict[str, Any]]) -> None:
    try:
        os.makedirs(os.path.dirname(LOCKOUT_FILE), exist_ok=True)
        raw = json.dumps(records).encode("utf-8")
        crypto = _get_crypto()
        if crypto:
            encrypted = crypto.encrypt_bytes(raw)
            with open(LOCKOUT_FILE, "wb") as f:
                f.write(encrypted)
        else:
            with open(LOCKOUT_FILE, "w", encoding="utf-8") as f:
                f.write(raw.decode("utf-8"))
    except Exception:
        pass

class AuthenticationService:
    """
    Service responsible for handling user authentication, 
    session validation, persistent lockout handling, and role checking via SecurityManager.
    """
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.current_user: Optional[User] = None
        self.security_manager = SecurityManager()

    def _hash_password(self, password: str) -> str:
        """Hash a password securely via PBKDF2-HMAC-SHA256."""
        return PasswordHasher.hash_password(password)

    def login(self, username: str, password: str) -> User:
        """
        Validate credentials and set current session.
        Raises AuthenticationError if invalid.
        """
        if not username or not password:
            raise ValidationError("Username and password are required.")

        now = time.time()
        records = _load_lockout_records()
        attempt_record = records.get(username, {'count': 0, 'lockout_until': 0.0})
        if attempt_record['lockout_until'] > now:
            wait_sec = int(attempt_record['lockout_until'] - now) + 1
            raise AuthenticationError(f"Too many failed login attempts. Account temporarily locked for {wait_sec} seconds.")

        user = self.user_repo.get_by_username(username)
        if not user:
            # Fallback check by email
            user = self.user_repo.session.query(User).filter_by(email=username).first()

        if not user or not PasswordHasher.verify_password(password, user.password_hash):
            count = attempt_record['count'] + 1
            lockout_time = 0.0
            if count >= 5:
                lockout_time = now + 60.0
                try:
                    from security.audit_trail import audit_logger
                    audit_logger.log_action("LOGIN_LOCKOUT", user_id=user.id if user else 0, user_email=username, details=f"Account locked due to {count} consecutive failed login attempts.")
                except Exception:
                    pass
            records[username] = {'count': count, 'lockout_until': lockout_time}
            _save_lockout_records(records)
            raise AuthenticationError("Invalid username or password.")

        if username in records:
            del records[username]
            _save_lockout_records(records)

        # Transparently upgrade legacy or low-iteration password hashes
        if PasswordHasher.needs_rehash(user.password_hash):
            user.password_hash = PasswordHasher.hash_password(password)
            if hasattr(self.user_repo, 'session') and self.user_repo.session:
                try:
                    self.user_repo.session.commit()
                except Exception:
                    pass

        if not user.is_active:
            raise AuthenticationError("User account is inactive.")

        self.current_user = user
        self.security_manager.current_session = self.security_manager.auth_manager.create_session(
            user_id=user.id,
            user_email=user.email or user.username,
            role=user.role or "Audit Partner"
        )
        self.security_manager.audit_logger.log_action(
            user_email=user.email or user.username,
            role=user.role or "Audit Partner",
            action="LOGIN_SUCCESS",
            details="User logged in successfully"
        )
        return user

    def logout(self) -> None:
        """Clear the current session and revoke token."""
        if self.security_manager.current_session:
            self.security_manager.auth_manager.revoke_session(self.security_manager.current_session.token_str)
            self.security_manager.current_session = None
        self.current_user = None

    def require_role(self, required_roles: list[str]) -> bool:
        """
        Check if the current user has one of the required roles.
        Raises AuthenticationError if unauthorized.
        """
        if not self.current_user:
            raise AuthenticationError("No user logged in.")
            
        if self.current_user.role not in required_roles:
            raise AuthenticationError(f"Insufficient permissions. Required roles: {required_roles}")
            
        return True
