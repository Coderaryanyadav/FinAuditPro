"""Authentication and user session management service."""

from finauditpro.application.security.rbac import UserSession
from finauditpro.domain.entities import RoleEnum, User
from finauditpro.domain.exceptions import ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
    verify_password,
)


class AuthService:
    """Service handling credential verification and authenticated user session creation."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        # Automatically ensure default administrator is present
        self.ensure_default_admin()

    def ensure_default_admin(self) -> User | None:
        """Seed default admin if no users exist in database."""
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            return repo.seed_default_admin_if_empty()

    def authenticate(self, username: str, password: str) -> UserSession:
        """Verify username and password against database and return UserSession."""
        cleaned_user = username.strip().lower()
        if not cleaned_user or not password:
            raise ValidationError("Username and password are required.")

        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            user = repo.get_by_username(cleaned_user)
            if not user:
                raise ValidationError("Invalid username or password.")

            if not user.is_active:
                raise ValidationError(
                    "This user account is inactive. Please contact your administrator."
                )

            if not verify_password(password, user.password_hash, user.salt):
                raise ValidationError("Invalid username or password.")

            return UserSession(
                user_id=user.id,
                username=user.username,
                role=user.role,
            )

    def create_user(
        self, username: str, password: str, role: RoleEnum = RoleEnum.ASSOCIATE
    ) -> User:
        """Create a new user with secure password hash."""
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            return repo.create_user_with_password(username, password, role)

    def list_users(self) -> list[User]:
        """List all registered users."""
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            return repo.list_all()
