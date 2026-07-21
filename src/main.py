import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.styles import GLOBAL_QSS
from ui.splash import SplashScreen
from ui.login import LoginWindow
from database.database import init_db

def main():
    # Initialize database
    init_db()
    
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)
    
    # Show splash screen first
    splash = SplashScreen()
    splash.show()
    
    # Define transition logic
    def show_login():
        splash.close()
        login = LoginWindow()
        login.show()
        # Keep login window reference alive
        app.active_window = login
        
    splash.finished.connect(show_login)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
