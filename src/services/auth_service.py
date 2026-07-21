import hashlib
import re
from typing import Optional
from core.exceptions import AuthenticationError, ValidationError
from database.repositories.user_repo import UserRepository
from database.models import User

class AuthenticationService:
    """
    Service responsible for handling user authentication, 
    session validation, and role checking.
    
    Repositories used:
    - UserRepository
    
    Business Rules:
    - Passwords must be hashed using SHA-256 (in production, use Argon2 or bcrypt).
    - Roles must be strictly checked before authorizing actions.
    """
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.current_user: Optional[User] = None

    def _hash_password(self, password: str) -> str:
        """Hash a password securely."""
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username: str, password: str) -> User:
        """
        Validate credentials and set current session.
        Raises AuthenticationError if invalid.
        """
        if not username or not password:
            raise ValidationError("Username and password are required.")

        user = self.user_repo.get_by_username(username)
        if not user:
            raise AuthenticationError("Invalid username or password.")
            
        hashed = self._hash_password(password)
        if user.password_hash != hashed:
            raise AuthenticationError("Invalid username or password.")
            
        if not user.is_active:
            raise AuthenticationError("User account is inactive.")

        self.current_user = user
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
