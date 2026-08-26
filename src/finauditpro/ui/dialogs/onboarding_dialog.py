"""
FinAuditPro Enterprise — First-Run Administrator Onboarding
Split-view onboarding window for setting up the initial administrator account.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.auth_service import AuthService
from finauditpro.domain.exceptions import ValidationError
from finauditpro.version import __version__


class OnboardingDialog(QDialog):
    """Enterprise First-Run Onboarding Window."""

    onboarding_successful = Signal(str, str)  # username, role

    def __init__(
        self,
        parent: QWidget | None = None,
        auth_service: AuthService | None = None,
    ) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.authenticated_session: UserSession | None = None
        self.setWindowTitle("FinAuditPro — Setup Administrator")

        self.resize(1020, 640)
        self.setMinimumSize(780, 540)
        self.setStyleSheet("background-color: #F7F8FA;")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT: Brand Panel ─────────────────────────────────────────
        left = QFrame()
        left.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f172a, stop:1 #1e293b);"
            "border-right: 1px solid #1e293b;"
        )
        ll = QVBoxLayout(left)
        ll.setContentsMargins(48, 52, 48, 40)
        ll.setSpacing(0)

        # Logo mark
        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(36, 36)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #007AFF; color: #ffffff; border-radius: 8px;"
            "font-size: 14px; font-weight: 800; border: none;"
        )
        logo_name = QLabel("FinAuditPro")
        logo_name.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #ffffff; border: none; background: transparent; margin-left: 10px;"
        )
        logo_row.addWidget(logo_box)
        logo_row.addWidget(logo_name)
        logo_row.addStretch()
        ll.addLayout(logo_row)
        ll.addStretch(1)

        # Headline
        h1 = QLabel("Welcome to\nFinAuditPro.")
        h1.setStyleSheet(
            "font-size: 34px; font-weight: 800; color: #ffffff; border: none; background: transparent;"
            "line-height: 1.2;"
        )
        h1.setWordWrap(True)
        ll.addWidget(h1)
        ll.addSpacing(14)

        sub = QLabel(
            "Before we begin, please create the primary administrator account for this local workspace."
        )
        sub.setStyleSheet(
            "font-size: 13px; color: #94a3b8; border: none; background: transparent; line-height: 1.5;"
        )
        sub.setWordWrap(True)
        ll.addWidget(sub)
        ll.addStretch(2)

        # Feature checklist
        features = [
            "Your data never leaves this machine",
            "Full control over user permissions",
            "Built-in compliance constraints",
        ]
        for f in features:
            row = QHBoxLayout()
            dot = QLabel("")
            dot.setStyleSheet(
                "font-size: 13px; color: #38BDF8; font-weight: 700; border: none; background: transparent;"
            )
            dot.setFixedWidth(20)
            tx = QLabel(f)
            tx.setStyleSheet(
                "font-size: 13px; color: #CBD5E1; font-weight: 400; border: none; background: transparent;"
            )
            row.addWidget(dot)
            row.addWidget(tx)
            row.addStretch()
            ll.addLayout(row)
            ll.addSpacing(8)

        ll.addStretch(3)

        ver = QLabel(f"Enterprise v{__version__} · First Run")
        ver.setStyleSheet("font-size: 11px; color: #64748b; border: none; background: transparent;")
        ll.addWidget(ver)

        # ── RIGHT: Form ───────────────────────────────────────────────
        right_bg = QWidget()
        right_bg.setStyleSheet("background-color: #F7F8FA;")
        rl = QVBoxLayout(right_bg)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form = QFrame()
        form.setFixedWidth(380)
        form.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; }"
        )

        fl = QVBoxLayout(form)
        fl.setContentsMargins(32, 32, 32, 32)
        fl.setSpacing(0)

        form_title = QLabel("Sign Up")
        form_title.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #111827; border: none; background: transparent;"
        )
        form_sub = QLabel("Create your master credentials.")
        form_sub.setStyleSheet(
            "font-size: 12px; color: #6B7280; margin-top: 4px; border: none; background: transparent;"
        )

        fl.addWidget(form_title)
        fl.addWidget(form_sub)
        fl.addSpacing(24)

        # Inputs
        lbl_e = QLabel("Email Address")
        lbl_e.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #374151; margin-bottom: 4px; border: none; background: transparent;"
        )
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Enter administrator email")
        self.input_user.setStyleSheet(
            "QLineEdit { border: 1.5px solid #D1D5DB; border-radius: 6px; padding: 10px 14px; background: #FFFFFF; color: #111827; font-size: 13px; }"
            "QLineEdit:focus { border-color: #007AFF; background: #FFFFFF; }"
        )

        lbl_p = QLabel("Create Password")
        lbl_p.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #374151; margin-top: 14px; margin-bottom: 4px; border: none; background: transparent;"
        )
        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Enter a secure password")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setStyleSheet(
            "QLineEdit { border: 1.5px solid #D1D5DB; border-radius: 6px; padding: 10px 14px; background: #FFFFFF; color: #111827; font-size: 13px; }"
            "QLineEdit:focus { border-color: #007AFF; background: #FFFFFF; }"
        )

        lbl_cp = QLabel("Confirm Password")
        lbl_cp.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #374151; margin-top: 14px; margin-bottom: 4px; border: none; background: transparent;"
        )
        self.input_cpass = QLineEdit()
        self.input_cpass.setPlaceholderText("Confirm your password")
        self.input_cpass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_cpass.setStyleSheet(
            "QLineEdit { border: 1.5px solid #D1D5DB; border-radius: 6px; padding: 10px 14px; background: #FFFFFF; color: #111827; font-size: 13px; }"
            "QLineEdit:focus { border-color: #007AFF; background: #FFFFFF; }"
        )

        toggle_login_pwd = QAction("Show", self.input_pass)
        self.input_pass.addAction(toggle_login_pwd, QLineEdit.ActionPosition.TrailingPosition)
        self.input_cpass.addAction(toggle_login_pwd, QLineEdit.ActionPosition.TrailingPosition)

        def _toggle_login_pwd_visibility() -> None:
            if self.input_pass.echoMode() == QLineEdit.EchoMode.Password:
                self.input_pass.setEchoMode(QLineEdit.EchoMode.Normal)
                self.input_cpass.setEchoMode(QLineEdit.EchoMode.Normal)
                toggle_login_pwd.setText("Hide")
            else:
                self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
                self.input_cpass.setEchoMode(QLineEdit.EchoMode.Password)
                toggle_login_pwd.setText("Show")

        toggle_login_pwd.triggered.connect(_toggle_login_pwd_visibility)

        fl.addWidget(lbl_e)
        fl.addWidget(self.input_user)
        fl.addWidget(lbl_p)
        fl.addWidget(self.input_pass)
        fl.addWidget(lbl_cp)
        fl.addWidget(self.input_cpass)
        fl.addSpacing(20)

        # Submit CTA
        self.btn_submit = QPushButton("Sign Up")
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.setStyleSheet(
            "QPushButton { background: #007AFF; color: #FFFFFF; border-radius: 6px; font-weight: 600; font-size: 14px; padding: 12px; border: none; }"
            "QPushButton:hover { background: #0056b3; }"
            "QPushButton:pressed { background: #004085; }"
        )
        self.btn_submit.clicked.connect(self._handle_onboarding)
        fl.addWidget(self.btn_submit)
        
        rl.addWidget(form)
        
        root.addWidget(left, stretch=4)
        root.addWidget(right_bg, stretch=5)

    def _handle_onboarding(self) -> None:
        """Handle onboarding submission."""
        email = self.input_user.text().strip()
        pwd = self.input_pass.text()
        cpwd = self.input_cpass.text()
        
        if not email or not pwd:
            QMessageBox.warning(self, "Validation Error", "Email and password are required.")
            return
            
        if pwd != cpwd:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            return

        try:
            if self.auth_service:
                session = self.auth_service.setup_initial_admin(email, pwd)
                self.authenticated_session = session
                self.onboarding_successful.emit(session.username, session.role.value)
                self.accept()
        except ValidationError as ex:
            QMessageBox.warning(self, "Validation Error", str(ex))
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {ex}")

    def get_session(self) -> UserSession | None:
        return self.authenticated_session
