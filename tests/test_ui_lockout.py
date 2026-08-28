"""UI automated tests for MainWindow inactivity lock and manual lock screen overlays."""

import os
import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from finauditpro.ui.main_window import MainWindow
from finauditpro.application.security.rbac import UserSession
from finauditpro.domain.entities import RoleEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager


def test_ui_inactivity_lock_and_unlock(monkeypatch, tmp_path) -> None:
    """Test that MainWindow locks on inactivity and unlocks with the correct passcode."""
    # Ensure a QApplication instance is initialized
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    import finauditpro.infrastructure.security.encryption as enc

    # Isolate key storage files to tmp_path
    monkeypatch.setattr(enc, "_get_key_file_path", lambda: tmp_path / "test_key.key")
    monkeypatch.setattr(enc, "_get_salt_file_path", lambda: tmp_path / "test_salt.bin")
    monkeypatch.setattr(enc, "_CIPHER", None)

    # Initialize encryption DEK
    passcode = "SecurePlatformPassword@2026"
    enc.initialize_wrapped_dek(passcode)

    # Force rapid inactivity timeout of 50ms for testing
    monkeypatch.setenv("FINAUDITPRO_INACTIVITY_TIMEOUT_MS", "50")

    # Set up database manager for window initialization
    db_manager = DatabaseManager(db_path=tmp_path / "test_lockout.db")
    db_manager.create_tables()

    # Instantiate MainWindow
    window = MainWindow(db_manager)
    window.show()

    window.current_user_session = UserSession(
        user_id="u1", username="auditor@firm.com", role=RoleEnum.ASSOCIATE
    )

    # Initial state
    assert window.current_user_session.is_locked is False
    assert not hasattr(window, "lock_screen_widget") or window.lock_screen_widget is None

    # Wait for the inactivity timer to trigger the lock overlay by running a local event loop
    loop = QEventLoop()
    QTimer.singleShot(150, loop.quit)
    loop.exec()

    # Assert locked state
    assert window.current_user_session.is_locked is True
    assert window.lock_screen_widget is not None
    assert window.lock_screen_widget.isVisible() is True

    # Try invalid unlock passcode -> remains locked
    window.lock_screen_widget.input_passcode.setText("WrongPasscode")
    window.lock_screen_widget._handle_unlock()
    assert window.current_user_session.is_locked is True

    # Try valid unlock passcode -> successfully unlocks
    window.lock_screen_widget.input_passcode.setText(passcode)
    window.lock_screen_widget._handle_unlock()

    # Assert unlocked state and overlay clean up
    assert window.current_user_session.is_locked is False
    assert not hasattr(window, "lock_screen_widget") or window.lock_screen_widget is None

    # Clean up window
    window.close()
