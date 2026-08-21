import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from ui.styles import get_qss
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
    """Clean light palette for native Qt dialogs using V2 design tokens."""
    from ui.theme import LightColors as C
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,           QColor(C.BG_BASE))
    p.setColor(QPalette.ColorRole.WindowText,       QColor(C.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.Base,             QColor(C.BG_SURFACE))
    p.setColor(QPalette.ColorRole.AlternateBase,    QColor(C.BG_SUBTLE))
    p.setColor(QPalette.ColorRole.Text,             QColor(C.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.BrightText,       QColor(C.BG_SURFACE))
    p.setColor(QPalette.ColorRole.Button,           QColor(C.BG_SURFACE))
    p.setColor(QPalette.ColorRole.ButtonText,       QColor(C.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.Highlight,        QColor(C.ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText,  QColor(C.BG_SURFACE))
    p.setColor(QPalette.ColorRole.ToolTipBase,      QColor(C.BG_SURFACE))
    p.setColor(QPalette.ColorRole.ToolTipText,      QColor(C.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.PlaceholderText,  QColor(C.TEXT_PLACEHOLDER))
    p.setColor(QPalette.ColorRole.Mid,              QColor(C.BORDER_DEFAULT))
    p.setColor(QPalette.ColorRole.Dark,             QColor(C.BG_BASE))
    p.setColor(QPalette.ColorRole.Shadow,           QColor("#000000"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window,     QColor(C.BG_SUBTLE))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(C.TEXT_DISABLED))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(C.TEXT_DISABLED))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       QColor(C.TEXT_DISABLED))
    return p


def _ensure_admin_user():
    """Create default admin user on first launch if no users exist (configurable via environment variables)."""
    import logging
    _log = logging.getLogger(__name__)
    try:
        from database.database import get_session
        from database.models import User
        from security.auth import PasswordHasher

        admin_email = os.environ.get("FINAUDIT_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL") or "admin@finauditpro.com"
        admin_pass = os.environ.get("FINAUDIT_ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or "Admin@123"
        admin_role = os.environ.get("FINAUDIT_ADMIN_ROLE") or os.environ.get("ADMIN_ROLE") or "Administrator"
        username_part = admin_email.split("@")[0]

        with get_session() as session:
            if session.query(User).count() == 0:
                hashed = PasswordHasher.hash_password(admin_pass)
                admin = User(
                    username=username_part,
                    email=admin_email,
                    password_hash=hashed,
                    role=admin_role,
                    is_active=True,
                )
                session.add(admin)
                session.commit()
                _log.info(f"First-run: Created default admin user ({admin_email}).")
    except Exception as e:
        _log.warning(f"Could not auto-create admin user: {e}")



def main():
    # 1. Enable High DPI Pixmap Scaling & Initialize QApplication FIRST
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # 2. Setup Enterprise Logging & Global Crash Interceptor
    setup_application_logging()
    setup_global_crash_handler()

    # 3. Database Schema Migration & Initialization
    init_db()
    DatabaseMigrator.migrate()

    # 4. Ensure at least one admin user exists (first-run)
    _ensure_admin_user()

    # 5. Security Manager & Background AI Pre-flight Bootstrap
    SecurityManager()
    EngineBootstrap.start_background_bootstrap()

    # Apply clean trustworthy light palette (covers native widgets like QMessageBox)
    app.setPalette(_build_light_palette())
    app.setStyleSheet(get_qss(dark=False))
    
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
        if hasattr(app, "login") and app.login and app.login.isVisible():
            app.login.close()

    def show_login():
        app.login = LoginWindow()
        app.login.login_successful.connect(show_dashboard)
        app.login.show()
        app.login.raise_()
        app.login.activateWindow()
        if hasattr(app, "splash") and app.splash and app.splash.isVisible():
            app.splash.close()
        
    app.splash.finished.connect(show_login)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
