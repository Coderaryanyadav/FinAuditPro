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

    @staticmethod
    def validate_password_complexity(password: str) -> None:
        """Validate password meets enterprise security standards."""
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        has_letter = any(c.isalpha() for c in password)
        has_number_or_symbol = any(c.isdigit() or not c.isalnum() for c in password)
        if not (has_letter and has_number_or_symbol):
            raise ValidationError(
                "Password must contain letters and at least one number or special character."
            )
        if password == "Admin@123":  # noqa: S105
            raise ValidationError(
                "New password cannot be the default administrator password (Admin@123)."
            )

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
                must_change_password=user.must_change_password,
            )

    def force_setup_credentials(
        self, user_id: str, new_email: str, new_password: str
    ) -> UserSession:
        """Update username/email and password during mandatory first login setup."""
        cleaned_email = new_email.strip().lower()
        if not cleaned_email or "@" not in cleaned_email:
            raise ValidationError("A valid email address is required.")
        self.validate_password_complexity(new_password)
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            user = repo.update_credentials(
                user_id,
                new_username=cleaned_email,
                new_password=new_password,
                must_change_password=False,
            )
            return UserSession(
                user_id=user.id,
                username=user.username,
                role=user.role,
                must_change_password=False,
            )

    def force_change_password(self, user_id: str, new_password: str) -> UserSession:
        """Force update user password and clear must_change_password flag."""
        self.validate_password_complexity(new_password)
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            user = repo.update_password(user_id, new_password, must_change_password=False)
            return UserSession(
                user_id=user.id,
                username=user.username,
                role=user.role,
                must_change_password=False,
            )

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> UserSession:
        """Change user password after verifying current credentials."""
        self.validate_password_complexity(new_password)
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if not user:
                raise ValidationError("User not found.")
            if not verify_password(old_password, user.password_hash, user.salt):
                raise ValidationError("Current password is incorrect.")
            updated_user = repo.update_password(user_id, new_password, must_change_password=False)
            return UserSession(
                user_id=updated_user.id,
                username=updated_user.username,
                role=updated_user.role,
                must_change_password=False,
            )

    def create_user(
        self,
        username: str,
        password: str,
        role: RoleEnum = RoleEnum.ASSOCIATE,
        must_change_password: bool = False,
    ) -> User:
        """Create a new user with secure password hash."""
        self.validate_password_complexity(password)
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            return repo.create_user_with_password(
                username, password, role, must_change_password=must_change_password
            )

    def list_users(self) -> list[User]:
        """List all registered users."""
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            return repo.list_all()
