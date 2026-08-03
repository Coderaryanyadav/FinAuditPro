import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from ui.styles import GLOBAL_QSS
from ui.splash import SplashScreen
from ui.login import LoginWindow
from ui.dashboard import DashboardWindow
from database.database import init_db
from deployment.logger import setup_application_logging
from deployment.crash_reporter import setup_global_crash_handler
from deployment.migration import DatabaseMigrator
from deployment.bootstrap import EngineBootstrap
from security.security_manager import SecurityManager


def _build_light_palette() -> QPalette:
    """Build a clean, trustworthy Light Sky Blue palette for native Qt dialogs."""
    p = QPalette()
    BG       = QColor("#f8fafc")
    SURFACE  = QColor("#ffffff")
    ELEVATED = QColor("#ffffff")
    TEXT     = QColor("#0f172a")
    MUTED    = QColor("#475569")
    DIM      = QColor("#94a3b8")
    ACCENT   = QColor("#0284c7")
    DISABLED = QColor("#f1f5f9")
    DIS_TEXT = QColor("#cbd5e1")

    p.setColor(QPalette.ColorRole.Window,           BG)
    p.setColor(QPalette.ColorRole.WindowText,       TEXT)
    p.setColor(QPalette.ColorRole.Base,             SURFACE)
    p.setColor(QPalette.ColorRole.AlternateBase,    QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Text,             TEXT)
    p.setColor(QPalette.ColorRole.BrightText,       QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.Button,           SURFACE)
    p.setColor(QPalette.ColorRole.ButtonText,       TEXT)
    p.setColor(QPalette.ColorRole.Highlight,        ACCENT)
    p.setColor(QPalette.ColorRole.HighlightedText,  QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ToolTipBase,      SURFACE)
    p.setColor(QPalette.ColorRole.ToolTipText,      TEXT)
    p.setColor(QPalette.ColorRole.PlaceholderText,  DIM)
    p.setColor(QPalette.ColorRole.Mid,              QColor("#e2e8f0"))
    p.setColor(QPalette.ColorRole.Dark,             BG)
    p.setColor(QPalette.ColorRole.Shadow,           QColor("#000000"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window,     DISABLED)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, DIS_TEXT)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, DIS_TEXT)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       DIS_TEXT)
    return p


def _ensure_admin_user():
    """Create default admin user on first launch if no users exist."""
    import logging
    _log = logging.getLogger(__name__)
    try:
        from database.database import get_session
        from database.models import User
        from security.auth import PasswordHasher
        with get_session() as session:
            if session.query(User).count() == 0:
                hashed = PasswordHasher.hash_password("Admin@123")
                admin = User(
                    username="admin",
                    email="admin@finauditpro.com",
                    password_hash=hashed,
                    role="Audit Partner",
                    is_active=True,
                )
                session.add(admin)
                session.commit()
                _log.info("First-run: Created default admin user (admin@finauditpro.com).")
    except Exception as e:
        _log.warning(f"Could not auto-create admin user: {e}")


def main():
    # 1. Setup Enterprise Logging & Global Crash Interceptor
    setup_application_logging()
    setup_global_crash_handler()

    # 2. Database Schema Migration & Initialization
    init_db()
    DatabaseMigrator.migrate()

    # 3. Ensure at least one admin user exists (first-run)
    _ensure_admin_user()

    # 4. Security Manager & Background AI Pre-flight Bootstrap
    SecurityManager()
    EngineBootstrap.start_background_bootstrap()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    # Apply clean trustworthy light palette (covers native widgets like QMessageBox)
    app.setPalette(_build_light_palette())
    app.setStyleSheet(GLOBAL_QSS)
    
    # Show splash screen first
    app.splash = SplashScreen()
    app.splash.show()
    app.splash.raise_()
    app.splash.activateWindow()
    
    def show_dashboard(user=None):
        app.dashboard = DashboardWindow(user=user)
        app.dashboard.show()
        app.dashboard.raise_()
        app.dashboard.activateWindow()
        if hasattr(app, "login"):
            app.login.close()
        app.setQuitOnLastWindowClosed(True)

    def show_login():
        app.login = LoginWindow()
        app.login.login_successful.connect(show_dashboard)
        app.login.show()
        app.login.raise_()
        app.login.activateWindow()
        if hasattr(app, "splash"):
            app.splash.close()
        app.setQuitOnLastWindowClosed(True)
        
    app.splash.finished.connect(show_login)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
