from typing import Callable
from fastapi import Depends, HTTPException, status
from database.models import User
from security.rbac import Permission, UserRole, RBACManager
from api.dependencies import get_current_user


def require_permission(permission: Permission) -> Callable:
    """Dependency factory returning a permission validator dependency."""

    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_str = current_user.role or "Junior Auditor"
        try:
            role_enum = UserRole(user_role_str)
        except ValueError:
            role_enum = UserRole.READ_ONLY

        if not RBACManager.has_permission(role_enum, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role_str}' lacks required permission '{permission.value}'"
            )
        return current_user

    return permission_checker
