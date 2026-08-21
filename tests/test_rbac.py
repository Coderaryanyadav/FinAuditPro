"""Unit tests for fail-closed RBAC security manager."""

import pytest

from finauditpro.application.security.rbac import RBACManager, UserSession
from finauditpro.domain.entities import RoleEnum
from finauditpro.domain.exceptions import PermissionDeniedError


def test_rbac_fail_closed_unauthenticated() -> None:
    rbac = RBACManager(session=None)
    assert rbac.check_permission("firm:create") is False

    with pytest.raises(PermissionDeniedError) as excinfo:
        rbac.require_permission("firm:create")
    assert "Unauthenticated" in str(excinfo.value)


def test_rbac_partner_permissions() -> None:
    session = UserSession(user_id="u1", username="partner1", role=RoleEnum.PARTNER)
    rbac = RBACManager(session=session)

    assert rbac.check_permission("firm:create") is True
    assert rbac.check_permission("engagement:signoff") is True
    rbac.require_permission("firm:create")  # Does not raise


def test_rbac_associate_permissions() -> None:
    session = UserSession(user_id="u2", username="assoc1", role=RoleEnum.ASSOCIATE)
    rbac = RBACManager(session=session)

    assert rbac.check_permission("document:upload") is True
    assert rbac.check_permission("firm:create") is False

    with pytest.raises(PermissionDeniedError):
        rbac.require_permission("firm:create")
