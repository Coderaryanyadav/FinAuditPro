"""Fail-closed Role-Based Access Control (RBAC) security manager."""

from dataclasses import dataclass

from finauditpro.domain.entities import RoleEnum
from finauditpro.domain.exceptions import PermissionDeniedError


@dataclass
class UserSession:
    user_id: str
    username: str
    role: RoleEnum
    must_change_password: bool = False
    is_locked: bool = False


_ROLE_PERMISSIONS: dict[RoleEnum, set[str]] = {
    RoleEnum.PARTNER: {
        "firm:create",
        "firm:edit",
        "client:create",
        "client:edit",
        "engagement:create",
        "engagement:edit",
        "engagement:delete",
        "engagement:signoff",
        "audit:review",
    },
    RoleEnum.MANAGER: {
        "client:create",
        "client:edit",
        "engagement:create",
        "engagement:edit",
        "audit:review",
        "audit:edit",
    },
    RoleEnum.SENIOR: {
        "engagement:edit",
        "audit:edit",
        "document:upload",
    },
    RoleEnum.ASSOCIATE: {
        "audit:view",
        "document:upload",
    },
}


class RBACManager:
    """Fail-closed access control manager. Denies all actions when no user session is active or session is locked."""

    def __init__(self, session: UserSession | None = None) -> None:
        self.current_session = session

    def lock_session(self) -> None:
        """Lock the current session."""
        if self.current_session:
            self.current_session.is_locked = True

    def unlock_session(self, passcode: str) -> None:
        """Unlock the session by re-verifying the passcode and re-initializing the encryption cipher."""
        if self.current_session:
            from finauditpro.infrastructure.security.encryption import initialize_session_cipher
            try:
                initialize_session_cipher(passcode)
                self.current_session.is_locked = False
            except Exception as ex:
                raise ValueError("Incorrect passcode. Failed to unlock session.") from ex

    def check_permission(self, permission: str) -> bool:
        """Return True if session exists, is not locked, and role holds permission, False otherwise."""
        if self.current_session is None or getattr(self.current_session, "is_locked", False):
            return False
        allowed = _ROLE_PERMISSIONS.get(self.current_session.role, set())
        return permission in allowed

    def require_permission(self, permission: str) -> None:
        """Raise PermissionDeniedError if session is missing or role is unprivileged."""
        if not self.check_permission(permission):
            role_name = (
                self.current_session.role.value
                if self.current_session
                else "None (Unauthenticated)"
            )
            raise PermissionDeniedError(
                f"Permission denied for action '{permission}'. Current active role: {role_name}."
            )
