"""Fail-closed Role-Based Access Control (RBAC) security manager."""

from dataclasses import dataclass

from finauditpro.domain.entities import RoleEnum
from finauditpro.domain.exceptions import PermissionDeniedError


@dataclass(frozen=True)
class UserSession:
    user_id: str
    username: str
    role: RoleEnum
    must_change_password: bool = False


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
    """Fail-closed access control manager. Denies all actions when no user session is active."""

    def __init__(self, session: UserSession | None = None) -> None:
        self.current_session = session

    def check_permission(self, permission: str) -> bool:
        """Return True if session exists and role holds permission, False otherwise."""
        if self.current_session is None:
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
