import time
from typing import Optional, Dict, Any
from core.exceptions import AuthenticationError, ValidationError
from database.repositories.user_repo import UserRepository
from database.models import User

from security.auth import PasswordHasher
from security.security_manager import SecurityManager

_failed_login_attempts: Dict[str, Dict[str, Any]] = {}

class AuthenticationService:
    """
    Service responsible for handling user authentication, 
    session validation, and role checking via SecurityManager.
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
        attempt_record = _failed_login_attempts.get(username, {'count': 0, 'lockout_until': 0.0})
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
            _failed_login_attempts[username] = {'count': count, 'lockout_until': lockout_time}
            raise AuthenticationError("Invalid username or password.")

        if username in _failed_login_attempts:
            del _failed_login_attempts[username]

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
