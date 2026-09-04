"""Thread-safe ambient SecurityContext for authenticated user session management."""

import contextvars
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


from finauditpro.application.security.rbac import UserSession

_current_session_var: contextvars.ContextVar[UserSession | None] = contextvars.ContextVar(
    "current_user_session", default=None
)


class SecurityContext:
    """Ambient Security Context providing trusted authentication state to application services."""

    @classmethod
    def set_current_session(cls, session: UserSession | None) -> None:
        """Set the active authenticated user session for the current context/thread."""
        _current_session_var.set(session)

    @classmethod
    def set_current_user(cls, user_id: str, role: Any = None) -> None:
        """Backward-compatibility helper setting active authenticated user session."""
        from finauditpro.domain.entities import RoleEnum
        role_enum = role if isinstance(role, RoleEnum) else (RoleEnum(str(role)) if role else RoleEnum.SENIOR)
        cls.set_current_session(UserSession(user_id=user_id, username=user_id, role=role_enum))


    @classmethod
    def get_current_session(cls) -> UserSession | None:
        """Retrieve the active authenticated user session."""
        return _current_session_var.get()

    @classmethod
    def get_current_user_id(cls) -> str | None:
        """Retrieve the authenticated user's ID if a valid session exists."""
        session = cls.get_current_session()
        return session.user_id if session else None

    @classmethod
    def get_current_username(cls) -> str | None:
        """Retrieve the authenticated username if a valid session exists."""
        session = cls.get_current_session()
        return session.username if session else None

    @classmethod
    def clear(cls) -> None:
        """Clear active security session context."""
        _current_session_var.set(None)

    @classmethod
    @contextmanager
    def with_session(cls, session: UserSession | None) -> Generator[None, None, None]:
        """Context manager to run a block with a trusted ambient security session."""
        token = _current_session_var.set(session)
        try:
            yield
        finally:
            _current_session_var.reset(token)
