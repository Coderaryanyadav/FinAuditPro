"""Automated unit tests for macOS Touch ID biometrics and Step-Up TOTP regulatory authorization."""

from PySide6.QtWidgets import QApplication

from finauditpro.application.security.rbac import RBACManager, UserSession
from finauditpro.domain.entities import RoleEnum, User
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.user_repository import UserRepository
from finauditpro.infrastructure.security.biometrics import (
    authenticate_with_biometrics,
    is_biometrics_available,
)
from finauditpro.infrastructure.security.totp import generate_totp_code, generate_totp_secret
from finauditpro.ui.dialogs.stepup_totp_dialog import StepUpTOTPDialog
from finauditpro.ui.widgets.lock_screen import LockScreenOverlay


def test_is_biometrics_available_functionality(monkeypatch) -> None:
    """Test biometrics detection and environment override flag."""
    # Test disable flag
    monkeypatch.setenv("FINAUDITPRO_DISABLE_BIOMETRICS", "1")
    assert is_biometrics_available() is False

    monkeypatch.delenv("FINAUDITPRO_DISABLE_BIOMETRICS", raising=False)
    avail = is_biometrics_available()
    assert isinstance(avail, bool)


def test_authenticate_with_biometrics_fallback(monkeypatch) -> None:
    """Test biometric evaluation fallback when disabled."""
    monkeypatch.setenv("FINAUDITPRO_DISABLE_BIOMETRICS", "1")
    assert authenticate_with_biometrics("Test Reason") is False


def test_stepup_totp_dialog_validation_flow(tmp_path) -> None:
    """Test StepUpTOTPDialog with valid and invalid TOTP tokens."""
    _app = QApplication.instance() or QApplication([])

    db = DatabaseManager(db_path=tmp_path / "test_stepup.db")
    db.create_tables()

    secret = generate_totp_secret()
    user_id = "partner-1"

    with db.session_scope() as session:
        user_repo = UserRepository(session)
        user_repo.add(
            User(
                id=user_id,
                username="partner@auditfirm.com",
                password_hash="testhash",
                salt="testsalt",
                role=RoleEnum.PARTNER,
                totp_secret=secret,
                is_totp_enabled=True,
            )
        )

    from finauditpro.application.services.auth_service import AuthService

    auth_svc = AuthService(db)
    session_obj = UserSession(
        user_id=user_id, username="partner@auditfirm.com", role=RoleEnum.PARTNER
    )

    dlg = StepUpTOTPDialog(
        parent=None,
        action_title="Authorize Statutory Report Sign-Off",
        action_description="Test statutory action authorization",
        auth_service=auth_svc,
        user_session=session_obj,
    )
    dlg.show()

    # 1. Invalid / incomplete token format
    dlg.input_totp.setText("123")
    dlg._handle_verify()
    assert dlg.is_authorized is False
    assert bool(dlg.lbl_error.text())

    # 2. Incorrect 6-digit code
    dlg.input_totp.setText("999999")
    dlg._handle_verify()
    assert dlg.is_authorized is False
    assert bool(dlg.lbl_error.text())

    # 3. Valid current 6-digit TOTP code
    valid_code = generate_totp_code(secret)
    dlg.input_totp.setText(valid_code)
    dlg._handle_verify()
    assert dlg.is_authorized is True

    dlg.close()


def test_lock_screen_biometric_unlock(tmp_path, monkeypatch) -> None:
    """Test LockScreenOverlay biometric unlock handler."""
    _app = QApplication.instance() or QApplication([])

    user_sess = UserSession(
        user_id="u1", username="auditor@firm.com", role=RoleEnum.PARTNER, is_locked=True
    )
    rbac_mgr = RBACManager(user_sess)

    overlay = LockScreenOverlay(parent=None, rbac_manager=rbac_mgr)

    # Mock biometric evaluation to return True
    import finauditpro.infrastructure.security.biometrics as bio_mod

    monkeypatch.setattr(bio_mod, "authenticate_with_biometrics", lambda reason: True)

    overlay._handle_touch_id_unlock()
    assert user_sess.is_locked is False
