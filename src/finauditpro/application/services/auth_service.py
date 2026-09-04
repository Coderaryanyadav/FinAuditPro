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

    def is_first_run(self) -> bool:
        """Check if this is a fresh database requiring initial admin setup."""
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            return repo.is_empty()

    def setup_initial_admin(self, email: str, password: str) -> UserSession:
        """Create the very first administrator account during onboarding."""
        cleaned_email = email.strip().lower()
        if not cleaned_email or "@" not in cleaned_email:
            raise ValidationError("A valid email address is required.")
        self.validate_password_complexity(password)
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            if not repo.is_empty():
                raise ValidationError("Administrator account already exists.")
            user = repo.create_user_with_password(
                username=cleaned_email,
                password=password,
                role=RoleEnum.ADMINISTRATOR,
                must_change_password=False,
            )
            return UserSession(
                user_id=user.id,
                username=user.username,
                role=user.role,
                must_change_password=user.must_change_password,
            )

    def reset_to_default_admin(self) -> None:
        """Reset default administrator credentials."""
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            user = repo.get_by_username("admin@finauditpro.com")
            if user:
                repo.update_credentials(
                    user.id,
                    new_password="Admin@123",  # noqa: S106
                    must_change_password=False,
                )
            else:
                repo.create_user_with_password(
                    "admin@finauditpro.com", "Admin@123", must_change_password=False
                )

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

    def authenticate(
        self, username: str, password: str, totp_token: str | None = None
    ) -> UserSession:
        """Verify username and password against database and return UserSession with lockout protection."""
        from finauditpro.infrastructure.security.lockout import (
            check_lockout,
            clear_failed_attempts,
            record_failed_attempt,
        )

        check_lockout()

        cleaned_user = username.strip().lower()
        if not cleaned_user or not password:
            raise ValidationError("Username and password are required.")

        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            user = repo.get_by_username(cleaned_user)
            if not user:
                record_failed_attempt()
                raise ValidationError("Invalid username or password.")

            if not user.is_active:
                raise ValidationError(
                    "This user account is inactive. Please contact your administrator."
                )

            if not verify_password(password, user.password_hash, user.salt):
                record_failed_attempt()
                raise ValidationError("Invalid username or password.")

            if user.is_totp_enabled:
                if not totp_token:
                    raise ValidationError("TOTP_REQUIRED")
                if not user.totp_secret or not self.verify_totp_token(user.totp_secret, totp_token):
                    record_failed_attempt()
                    raise ValidationError("Invalid 2FA token.")

            clear_failed_attempts()
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
            user = repo.get_by_id(user_id)
            if not user:
                raise ValidationError("User not found.")
            existing = repo.get_by_username(cleaned_email)
            if existing and existing.id != user_id:
                raise ValidationError(
                    f"Email {cleaned_email} is already registered to another account."
                )
            updated = repo.update_credentials(
                user_id=user_id,
                new_username=cleaned_email,
                new_password=new_password,
                must_change_password=False,
            )
            return UserSession(
                user_id=updated.id,
                username=updated.username,
                role=updated.role,
                must_change_password=False,
            )

    def update_user_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> UserSession:
        """Verify existing password and set new password."""
        self.validate_password_complexity(new_password)
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            user = repo.get_by_id(user_id)
            if not user:
                raise ValidationError("User not found.")
            if not verify_password(old_password, user.password_hash, user.salt):
                raise ValidationError("Current password does not match.")
            updated = repo.update_password(
                user_id=user_id, new_password=new_password, must_change_password=False
            )
            return UserSession(
                user_id=updated.id,
                username=updated.username,
                role=updated.role,
                must_change_password=False,
            )

    def change_password(self, user_id: str, old_password: str, new_password: str) -> UserSession:
        """Change user password after verifying current credentials."""
        return self.update_user_password(user_id, old_password, new_password)

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
        """Return list of all registered users."""
        with self.db_manager.session_scope() as session:
            repo = UserRepository(session)
            return repo.list_all()

    def generate_totp_secret(self) -> str:
        """Generate a new secure TOTP base32 secret."""
        from finauditpro.infrastructure.security.totp import generate_totp_secret

        return generate_totp_secret()

    def get_totp_uri(self, secret: str, username: str) -> str:
        """Generate provisioning URI for QR code generation."""
        from finauditpro.infrastructure.security.totp import get_totp_uri

        return get_totp_uri(secret, username)

    def verify_totp_token(self, secret: str, token: str) -> bool:
        """Verify a 6-digit TOTP token against a secret."""
        from finauditpro.infrastructure.security.totp import verify_totp_token

        return verify_totp_token(secret, token)

    def enable_totp(self, user_id: str, secret: str, token: str) -> bool:
        """Verify token and permanently enable TOTP for the user."""
        if not self.verify_totp_token(secret, token):
            raise ValidationError("Invalid 2FA token.")

        with self.db_manager.session_scope() as session:
            from finauditpro.infrastructure.persistence.models import UserModel

            model = session.get(UserModel, user_id)
            if not model:
                raise ValidationError("User not found.")
            model.totp_secret = secret
            model.is_totp_enabled = True
            session.flush()
        return True

    def disable_totp(self, user_id: str) -> None:
        """Disable TOTP for the user."""
        with self.db_manager.session_scope() as session:
            from finauditpro.infrastructure.persistence.models import UserModel

            model = session.get(UserModel, user_id)
            if not model:
                raise ValidationError("User not found.")
            model.totp_secret = None
            model.is_totp_enabled = False
            session.flush()

    def is_totp_enabled_for_user(self, user_id: str) -> bool:
        """Check if 2FA is active for given user ID without direct persistence calls from UI."""
        with self.db_manager.session_scope() as session:
            user = UserRepository(session).get_by_id(user_id)
            return bool(user and user.is_totp_enabled)

    def verify_user_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token for a specific user ID."""
        with self.db_manager.session_scope() as session:
            user = UserRepository(session).get_by_id(user_id)
            if not user or not user.is_totp_enabled or not user.totp_secret:
                return True
            return self.verify_totp_token(user.totp_secret, token)
