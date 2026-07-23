import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
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

def main():
    # 1. Setup Enterprise Logging & Global Crash Interceptor
    setup_application_logging()
    setup_global_crash_handler()

    # 2. Database Schema Migration & Initialization
    init_db()
    DatabaseMigrator.migrate()

    # 3. Security Manager & Background AI Pre-flight Bootstrap
    SecurityManager()
    EngineBootstrap.start_background_bootstrap()

    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)
    
    # Show splash screen first
    splash = SplashScreen()
    splash.show()
    
    def show_dashboard():
        dashboard = DashboardWindow()
        dashboard.show()
        app.active_window = dashboard

    def show_login():
        splash.close()
        login = LoginWindow()
        login.login_successful.connect(show_dashboard)
        login.show()
        app.active_window = login
        
    splash.finished.connect(show_login)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
