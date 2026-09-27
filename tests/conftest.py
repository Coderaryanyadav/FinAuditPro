import pytest
from unittest.mock import MagicMock

from finauditpro.application.security.security_context import SecurityContext

try:
    from PySide6.QtWidgets import QMessageBox
    _HAS_QT = True
except ImportError:
    _HAS_QT = False


@pytest.fixture(autouse=True)
def reset_security_context():
    SecurityContext.clear()
    try:
        from finauditpro.infrastructure.security.lockout import clear_failed_attempts
        clear_failed_attempts()
    except Exception:
        pass
    yield
    SecurityContext.clear()
    try:
        from finauditpro.infrastructure.security.lockout import clear_failed_attempts
        clear_failed_attempts()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def auto_mock_qmessagebox(monkeypatch):
    if _HAS_QT:
        monkeypatch.setattr(QMessageBox, "information", MagicMock(return_value=QMessageBox.StandardButton.Ok))
        monkeypatch.setattr(QMessageBox, "warning", MagicMock(return_value=QMessageBox.StandardButton.Ok))
        monkeypatch.setattr(QMessageBox, "critical", MagicMock(return_value=QMessageBox.StandardButton.Ok))
        monkeypatch.setattr(QMessageBox, "question", MagicMock(return_value=QMessageBox.StandardButton.Yes))
    yield

