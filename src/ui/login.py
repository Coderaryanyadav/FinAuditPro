from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QFrame)
from PySide6.QtCore import Qt, Signal, QTimer

class LoginWindow(QWidget):
    login_successful = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinAuditPro - Login")
        self.resize(900, 600)
        self.setObjectName("appBg")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Panel (White with abstract F logo placeholder)
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_label = QLabel("FinAuditPro")
        logo_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #0f172a; border: none;")
        left_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Intelligent Workspace")
        subtitle.setStyleSheet("font-size: 16px; color: #64748b; border: none;")
        left_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Right Panel (Login form)
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #f8fafc; border: none;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_container = QWidget()
        form_container.setFixedWidth(360)
        form_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(30, 40, 30, 40)
        form_layout.setSpacing(15)
        
        welcome_lbl = QLabel("Welcome Back")
        welcome_lbl.setStyleSheet("font-size: 26px; font-weight: bold; color: #0f172a; border: none;")
        
        sub_lbl = QLabel("Login to access your intelligent audit workspace.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #64748b; border: none; margin-bottom: 10px;")
        sub_lbl.setWordWrap(True)
        
        email_lbl = QLabel("Email Address")
        email_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #0f172a; border: none;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email Address")
        
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #0f172a; border: none;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 5, 0, 10)
        self.remember_cb = QCheckBox("Remember Me")
        self.remember_cb.setStyleSheet("border: none; background: transparent;")
        forgot_lbl = QLabel("<a href='#' style='color: #0b57d0; text-decoration: none;'>Forgot Password</a>")
        forgot_lbl.setOpenExternalLinks(False)
        forgot_lbl.setStyleSheet("border: none; font-size: 13px; background: transparent;")
        
        options_layout.addWidget(self.remember_cb)
        options_layout.addStretch()
        options_layout.addWidget(forgot_lbl)
        
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        
        offline_lbl = QLabel("<a href='#' style='color: #0b57d0; text-decoration: none;'>Continue Offline</a>")
        offline_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        offline_lbl.setStyleSheet("border: none; font-size: 13px; margin-top: 10px; background: transparent;")
        
        form_layout.addWidget(welcome_lbl)
        form_layout.addWidget(sub_lbl)
        form_layout.addWidget(email_lbl)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(pass_lbl)
        form_layout.addWidget(self.password_input)
        form_layout.addLayout(options_layout)
        form_layout.addWidget(self.login_btn)
        form_layout.addWidget(offline_lbl)
        
        right_layout.addWidget(form_container)
        
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=1)

    def handle_login(self):
        email = self.email_input.text()
        password = self.password_input.text()
        if email and password:
            self.login_btn.setText("Signing In...")
            self.login_btn.setDisabled(True)
            # Simulate DB Auth network/auth delay
            QTimer.singleShot(1000, self.auth_success)
    
    def auth_success(self):
        self.login_successful.emit()
        self.close()
