from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal
from sqlalchemy.exc import SQLAlchemyError
from .styles import apply_shadow

class LoginWindow(QWidget):
    login_successful = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinAuditPro - Auditor Login")
        self.resize(960, 620)
        self.setObjectName("appBg")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left Panel (Dark Corporate Slate Hero Panel)
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b);
                border-right: 1px solid #334155;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 50, 40, 50)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        badge = QLabel("🛡️ ICAI COMPLIANT & AIR-GAPPED")
        badge.setStyleSheet("""
            background-color: rgba(14, 165, 233, 0.15);
            color: #38bdf8;
            font-size: 11px;
            font-weight: 800;
            padding: 6px 12px;
            border-radius: 12px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            letter-spacing: 0.5px;
        """)
        left_layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignLeft)
        left_layout.addSpacing(16)
        
        logo_label = QLabel("FinAuditPro")
        logo_label.setStyleSheet("font-size: 38px; font-weight: 900; color: #ffffff; border: none; letter-spacing: -0.5px;")
        left_layout.addWidget(logo_label)
        
        subtitle = QLabel("Intelligent Audit & Compliance Workspace")
        subtitle.setStyleSheet("font-size: 16px; font-weight: 600; color: #38bdf8; border: none; margin-bottom: 24px;")
        left_layout.addWidget(subtitle)
        
        def create_feature_bullet(icon, text):
            row = QHBoxLayout()
            row.setSpacing(12)
            ic_lbl = QLabel(icon)
            ic_lbl.setStyleSheet("font-size: 16px; border: none;")
            tx_lbl = QLabel(text)
            tx_lbl.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: 500; border: none;")
            row.addWidget(ic_lbl)
            row.addWidget(tx_lbl)
            row.addStretch()
            return row

        left_layout.addLayout(create_feature_bullet("🔒", "100% Local RAG & LLM Analysis (Air-Gapped)"))
        left_layout.addSpacing(10)
        left_layout.addLayout(create_feature_bullet("⚡", "Automated Working Paper & Audit Trail Generation"))
        left_layout.addSpacing(10)
        left_layout.addLayout(create_feature_bullet("📊", "Statutory, GST & Tax Reconciliation Engine"))
        left_layout.addStretch()
        
        version_lbl = QLabel("FinAuditPro Enterprise v2.4.0 • Local Machine Deployment")
        version_lbl.setStyleSheet("font-size: 11px; color: #64748b; border: none;")
        left_layout.addWidget(version_lbl)
        
        # Right Panel (Login form)
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #f8fafc; border: none;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_container = QFrame()
        form_container.setFixedWidth(380)
        form_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
        """)
        apply_shadow(form_container, blur=24, dy=4, alpha=15)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(36, 40, 36, 40)
        form_layout.setSpacing(16)
        
        welcome_lbl = QLabel("Auditor Login")
        welcome_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; border: none;")
        
        sub_lbl = QLabel("Sign in to access your intelligent audit workspace.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #64748b; border: none; margin-bottom: 8px;")
        sub_lbl.setWordWrap(True)
        
        email_lbl = QLabel("Email Address")
        email_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155; border: none;")
        self.email_input = QLineEdit()
        self.email_input.setText("admin@finauditpro.com")
        self.email_input.setPlaceholderText("admin@finauditpro.com")
        self.email_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                background-color: #ffffff;
                font-size: 13px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 2px solid #0ea5e9;
            }
        """)
        
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155; border: none;")
        self.password_input = QLineEdit()
        self.password_input.setText("admin123")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                background-color: #ffffff;
                font-size: 13px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 2px solid #0ea5e9;
            }
        """)
        
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 4, 0, 8)
        self.remember_cb = QCheckBox("Remember Me")
        self.remember_cb.setChecked(True)
        self.remember_cb.setStyleSheet("border: none; background: transparent; color: #475569; font-size: 12px;")
        
        forgot_lbl = QLabel("<a href='#' style='color: #0ea5e9; text-decoration: none; font-weight: 600;'>Forgot Password?</a>")
        forgot_lbl.setOpenExternalLinks(False)
        forgot_lbl.setStyleSheet("border: none; font-size: 12px; background: transparent;")
        forgot_lbl.linkActivated.connect(self.handle_forgot_password)
        
        options_layout.addWidget(self.remember_cb)
        options_layout.addStretch()
        options_layout.addWidget(forgot_lbl)
        
        self.login_btn = QPushButton("Sign In to Workspace")
        self.login_btn.setFixedHeight(44)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0ea5e9;
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0284c7;
            }
            QPushButton:pressed {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                color: #e2e8f0;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        
        offline_lbl = QLabel("<a href='#' style='color: #64748b; text-decoration: none; font-size: 12px;'>🔒 Air-Gapped Local Mode</a>")
        offline_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        offline_lbl.setStyleSheet("border: none; margin-top: 6px; background: transparent;")
        offline_lbl.linkActivated.connect(self.handle_offline_mode)
        
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
        
        main_layout.addWidget(left_panel, stretch=5)
        main_layout.addWidget(right_panel, stretch=6)

    def handle_forgot_password(self, link=None):
        QMessageBox.information(
            self,
            "Password Reset",
            "FinAuditPro operates offline. To reset auditor account passwords, contact your System Administrator or execute password hashing via CLI."
        )

    def handle_offline_mode(self, link=None):
        QMessageBox.information(
            self,
            "Air-Gapped Offline Mode",
            "FinAuditPro runs 100% offline with zero cloud dependency.\n\nAll AI models, databases, and logs remain on local disk."
        )

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both email and password.")
            return

        self.login_btn.setText("Signing In...")
        self.login_btn.setDisabled(True)

        session = None
        try:
            from database.database import SessionLocal
            from database.repositories.user_repo import UserRepository
            from services.auth_service import AuthenticationService
            from database.models import User
            from security.auth import PasswordHasher

            session = SessionLocal()
            user_repo = UserRepository(session)
            
            # Seed default admin user if DB has 0 users
            if session.query(User).count() == 0:
                admin_user = User(
                    username="admin",
                    email="admin@finauditpro.com",
                    password_hash=PasswordHasher.hash_password("admin123"),
                    role="Audit Partner",
                    is_active=True
                )
                session.add(admin_user)
                session.commit()

            auth_service = AuthenticationService(user_repo)
            auth_service.login(email, password)
            self.auth_success()
        except (SQLAlchemyError, ValueError) as e:
            self.login_btn.setText("Sign In to Workspace")
            self.login_btn.setEnabled(True)
            QMessageBox.warning(self, "Authentication Failed", str(e))
        finally:
            if session:
                session.close()

    def auth_success(self):
        self.login_successful.emit()
        self.close()
