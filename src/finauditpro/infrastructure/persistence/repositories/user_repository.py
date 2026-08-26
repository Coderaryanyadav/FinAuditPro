"""User repository for SQLite persistence and secure credential verification."""

import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.entities import RoleEnum, User
from finauditpro.infrastructure.persistence.models import UserModel


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Generate PBKDF2-HMAC-SHA256 hash and random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return dk.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password against stored hash and salt in constant time."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return secrets.compare_digest(dk.hex(), password_hash)


class UserRepository:
    """Repository managing User persistence operations and credential checks."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            password_hash=model.password_hash,
            salt=model.salt,
            role=RoleEnum(model.role),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def add(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            username=user.username,
            password_hash=user.password_hash,
            salt=user.salt,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def get_by_id(self, user_id: str) -> User | None:
        model = self.session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    def get_by_username(self, username: str) -> User | None:
        cleaned = username.strip().lower()
        stmt = select(UserModel).where(UserModel.username == cleaned)
        model = self.session.scalars(stmt).first()
        return self._to_entity(model) if model else None

    def list_all(self) -> list[User]:
        stmt = select(UserModel).order_by(UserModel.username.asc())
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def create_user_with_password(
        self, username: str, password: str, role: RoleEnum = RoleEnum.ASSOCIATE
    ) -> User:
        cleaned = username.strip().lower()
        existing = self.get_by_username(cleaned)
        if existing:
            raise ValueError(f"User '{cleaned}' already exists.")
        pwd_hash, salt = hash_password(password)
        user = User(
            username=cleaned,
            password_hash=pwd_hash,
            salt=salt,
            role=role,
        )
        return self.add(user)

    def seed_default_admin_if_empty(self) -> User | None:
        """Seed default admin user (admin@finauditpro.com / Admin@123) if users table is empty."""
        stmt = select(UserModel).limit(1)
        first_user = self.session.scalars(stmt).first()
        if not first_user:
            return self.create_user_with_password(
                username="admin@finauditpro.com",
                password="Admin@123",  # noqa: S106
                role=RoleEnum.ADMINISTRATOR,
            )
        return None
