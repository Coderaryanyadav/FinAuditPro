import hashlib
import re
from typing import Optional
from core.exceptions import AuthenticationError, ValidationError
from database.repositories.user_repo import UserRepository
from database.models import User

from security.auth import PasswordHasher
from security.security_manager import SecurityManager

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

        user = self.user_repo.get_by_username(username)
        if not user:
            # Fallback check by email
            user = self.user_repo.session.query(User).filter_by(email=username).first()

        if not user:
            raise AuthenticationError("Invalid username or password.")

        # Verify password hash securely (PBKDF2-HMAC-SHA256)
        is_valid = PasswordHasher.verify_password(password, user.password_hash)
        if not is_valid:
            # Check legacy unhashed fallback if present and upgrade hash
            if user.password_hash == password:
                is_valid = True
                user.password_hash = PasswordHasher.hash_password(password)
                self.user_repo.session.commit()

        if not is_valid:
            raise AuthenticationError("Invalid username or password.")

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
        """Clear the current session."""
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
