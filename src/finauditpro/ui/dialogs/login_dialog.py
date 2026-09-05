"""
FinAuditPro Enterprise — Auditor Login Dialog
Split-view authentication window with crisp Apple typography and slate navy panel.
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


class LoginDialog(QDialog):
    """Enterprise Auditor Login Window — Split Navy & White Surface Design."""

    login_successful = Signal(str, str)  # username, role

    def __init__(
        self,
        parent: QWidget | None = None,
        auth_service: AuthService | None = None,
    ) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.authenticated_session: UserSession | None = None
        self.setWindowTitle("FinAuditPro — Statutory Audit Platform")

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
        h1 = QLabel("Built for\nstatutory auditors.")
        h1.setStyleSheet(
            "font-size: 34px; font-weight: 800; color: #ffffff; border: none; background: transparent;"
            "line-height: 1.2;"
        )
        h1.setWordWrap(True)
        ll.addWidget(h1)
        ll.addSpacing(14)

        sub = QLabel(
            "Automated working papers, AI-assisted analytics,\nCARO 2020 & GST reconciliation — all offline, all local."
        )
        sub.setStyleSheet(
            "font-size: 13px; color: #94a3b8; border: none; background: transparent; line-height: 1.5;"
        )
        sub.setWordWrap(True)
        ll.addWidget(sub)
        ll.addStretch(2)

        # Feature checklist
        features = [
            "100% air-gapped — no cloud dependency",
            "SA 230 compliant electronic working papers",
            "ICAI statutory audit workflows (CARO 2020)",
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

        ver = QLabel(f"Enterprise v{__version__} · Local deployment")
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

        form_title = QLabel("Sign in to FinAuditPro")
        form_title.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #111827; border: none; background: transparent;"
        )
        form_sub = QLabel("Enter your credentials to access the workspace.")
        form_sub.setStyleSheet(
            "font-size: 12px; color: #6B7280; margin-top: 4px; border: none; background: transparent;"
        )

        fl.addWidget(form_title)
        fl.addWidget(form_sub)
        fl.addSpacing(24)

        # Inputs
        lbl_e = QLabel("Email / Username")
        lbl_e.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #374151; margin-bottom: 4px; border: none; background: transparent;"
        )
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Enter your email")
        self.input_user.setStyleSheet(
            "QLineEdit { border: 1.5px solid #D1D5DB; border-radius: 6px; padding: 10px 14px; background: #FFFFFF; color: #111827; font-size: 13px; }"
            "QLineEdit:focus { border-color: #007AFF; background: #FFFFFF; }"
        )

        lbl_p = QLabel("Password")
        lbl_p.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #374151; margin-top: 14px; margin-bottom: 4px; border: none; background: transparent;"
        )
        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Enter your password")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setStyleSheet(
            "QLineEdit { border: 1.5px solid #D1D5DB; border-radius: 6px; padding: 10px 14px; background: #FFFFFF; color: #111827; font-size: 13px; }"
            "QLineEdit:focus { border-color: #007AFF; background: #FFFFFF; }"
        )

        toggle_login_pwd = QAction("Show", self.input_pass)
        self.input_pass.addAction(toggle_login_pwd, QLineEdit.ActionPosition.TrailingPosition)

        def _toggle_login_pwd_visibility() -> None:
            if self.input_pass.echoMode() == QLineEdit.EchoMode.Password:
                self.input_pass.setEchoMode(QLineEdit.EchoMode.Normal)
                toggle_login_pwd.setText("Hide")
            else:
                self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
                toggle_login_pwd.setText("Show")

        toggle_login_pwd.triggered.connect(_toggle_login_pwd_visibility)

        self.input_totp = QLineEdit()
        self.input_totp.setPlaceholderText("6-Digit 2FA Code")
        self.input_totp.setMaxLength(6)
        self.input_totp.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_totp.setStyleSheet(
            "QLineEdit { border: 1px solid #CBD5E1; border-radius: 6px; padding: 10px 14px; font-size: 13px; background: #FFFFFF; color: #0F172A; }"
            "QLineEdit:focus { border-color: #2563EB; }"
        )
        self.input_totp.setVisible(False)
        self.input_totp.returnPressed.connect(self._handle_login)

        fl.addWidget(lbl_e)
        fl.addWidget(self.input_user)
        fl.addWidget(lbl_p)
        fl.addWidget(self.input_pass)
        fl.addWidget(self.input_totp)
        fl.addSpacing(20)

        self.btn_submit = QPushButton("Sign In")
        self.btn_submit.setFixedHeight(40)
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.setStyleSheet(
            "QPushButton { background-color: #007AFF; color: #FFFFFF; font-size: 13px; font-weight: 600; border-radius: 6px; border: 1px solid transparent; }"
            "QPushButton:hover { background-color: #0062CC; border: 1px solid transparent; }"
        )
        self.btn_submit.clicked.connect(self._handle_login)

        fl.addWidget(self.btn_submit)
        fl.addSpacing(14)

        hint = QLabel("Fully offline · No data leaves your machine")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            "font-size: 11px; color: #64748b; line-height: 1.4; border: none; background: transparent;"
        )
        fl.addWidget(hint)

        rl.addWidget(form)

        root.addWidget(left, 45)
        root.addWidget(right_bg, 55)

    def _handle_login(self) -> None:
        user = self.input_user.text().strip()
        pwd = self.input_pass.text().strip()
        totp = self.input_totp.text().strip() if self.input_totp.isVisible() else None

        if not user or not pwd:
            QMessageBox.warning(
                self, "Validation Error", "Please enter both username and password."
            )
            return

        if not self.auth_service:
            self.login_successful.emit(user, "Administrator")
            self.accept()
            return

        try:
            session = self.auth_service.authenticate(user, pwd, totp_token=totp)
            if session.must_change_password:
                from finauditpro.ui.dialogs.change_password_dialog import ChangePasswordDialog

                pwd_dialog = ChangePasswordDialog(
                    parent=self,
                    auth_service=self.auth_service,
                    user_session=session,
                    is_forced=True,
                )
                if pwd_dialog.exec() != QDialog.DialogCode.Accepted:
                    QMessageBox.warning(
                        self,
                        "Security Requirement",
                        "You must set a new master password before accessing FinAuditPro.",
                    )
                    return
                if pwd_dialog.updated_session:
                    session = pwd_dialog.updated_session

            self.authenticated_session = session
            role_str = session.role.value if hasattr(session.role, "value") else str(session.role)
            self.login_successful.emit(session.username, role_str)
            self.accept()
        except ValidationError as ex:
            if str(ex) == "TOTP_REQUIRED":
                self.input_totp.setVisible(True)
                self.input_user.setEnabled(False)
                self.input_pass.setEnabled(False)
                self.btn_submit.setText("Verify 2FA")
                self.input_totp.setFocus()
            else:
                QMessageBox.warning(self, "Authentication Failed", str(ex))
        except Exception as ex:
            QMessageBox.critical(self, "Login Error", f"An unexpected error occurred: {ex}")

