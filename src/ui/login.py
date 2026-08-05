"""
FinAuditPro — Login Screen
Design language: Trustworthy Light Sky Blue — clean, modern, high-contrast.
Left: brand panel with clear typography and trust indicators.
Right: enterprise login form with crisp inputs and primary blue CTA.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFrame, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from database.database import get_session
from database.repositories.user_repo import UserRepository
from services.auth_service import AuthenticationService
from .styles import apply_shadow


# ── Shared field styles ───────────────────────────────────────────────────────
_INPUT = """
    QLineEdit {
        border: 1px solid #e5e5ea;
        border-radius: 8px;
        padding: 10px 14px;
        background-color: #f5f5f7;
        font-size: 13px;
        color: #1d1d1f;
    }
    QLineEdit:focus {
        border-color: #007aff;
        background-color: #ffffff;
    }
    QLineEdit:hover { border-color: #c7c7cc; }
"""

_COMBO = """
    QComboBox {
        border: 1px solid #e5e5ea;
        border-radius: 8px;
        padding: 10px 14px;
        background-color: #f5f5f7;
        font-size: 13px;
        color: #1d1d1f;
        font-weight: 400;
    }
    QComboBox:focus  { border-color: #007aff; background-color: #ffffff; }
    QComboBox:hover  { border-color: #c7c7cc; }
    QComboBox::drop-down { border: none; width: 26px; }
    QComboBox QAbstractItemView {
        background: #ffffff;
        border: 1px solid #e5e5ea;
        color: #1d1d1f;
        selection-background-color: #007aff;
        selection-color: #ffffff;
        outline: none;
        padding: 4px;
    }
"""


class LoginWindow(QWidget):
    """Enterprise Auditor Login Window."""
    login_successful = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinAuditPro — Statutory Audit Platform")
        self.resize(1080, 680)
        self.setObjectName("appBg")
        self.setMinimumSize(780, 560)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT: brand panel ────────────────────────────────────────
        left = QFrame()
        left.setObjectName("loginHeroPanel")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(56, 60, 56, 48)
        ll.setSpacing(0)

        # logo mark
        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(34, 34)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #007aff; color: #fff; border-radius: 8px;"
            "font-size: 13px; font-weight: 800; border: none;"
        )
        logo_name = QLabel("FinAuditPro")
        logo_name.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #1d1d1f; border: none; margin-left: 10px;"
        )
        logo_row.addWidget(logo_box)
        logo_row.addWidget(logo_name)
        logo_row.addStretch()
        ll.addLayout(logo_row)
        ll.addStretch(1)

        # headline
        h1 = QLabel("Built for\nstatutory auditors.")
        h1.setStyleSheet(
            "font-size: 36px; font-weight: 700; color: #1d1d1f; border: none; line-height: 1.2; letter-spacing: -0.8px;"
        )
        h1.setWordWrap(True)
        ll.addWidget(h1)
        ll.addSpacing(16)

        sub = QLabel(
            "Automated working papers, AI-assisted findings,\nGST reconciliation — all offline, all secure."
        )
        sub.setStyleSheet("font-size: 14px; color: #6e6e73; border: none; line-height: 1.5;")
        sub.setWordWrap(True)
        ll.addWidget(sub)
        ll.addStretch(2)

        # feature list
        features = [
            "100% air-gapped — no cloud dependency",
            "RBAC with Ed25519 audit trail signing",
            "ICAI compliant statutory audit workflows",
        ]
        for f in features:
            row = QHBoxLayout()
            dot = QLabel("✓")
            dot.setStyleSheet("font-size: 13px; color: #007aff; border: none; font-weight: 700;")
            dot.setFixedWidth(20)
            tx = QLabel(f)
            tx.setStyleSheet("font-size: 13px; color: #1d1d1f; border: none; font-weight: 500;")
            row.addWidget(dot)
            row.addWidget(tx)
            row.addStretch()
            ll.addLayout(row)
            ll.addSpacing(10)

        ll.addStretch(3)

        # version footer
        ver = QLabel("Enterprise v2.4.0 · Local deployment")
        ver.setStyleSheet("font-size: 11px; color: #86868b; border: none;")
        ll.addWidget(ver)

        # ── RIGHT: form ───────────────────────────────────────────────
        right_bg = QWidget()
        right_bg.setObjectName("loginRightBg")
        rl = QVBoxLayout(right_bg)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.setContentsMargins(52, 40, 52, 40)

        form = QFrame()
        form.setObjectName("loginFormContainer")
        form.setFixedWidth(400)
        apply_shadow(form, blur=24, dy=8, alpha=15)

        fl = QVBoxLayout(form)
        fl.setContentsMargins(36, 36, 36, 36)
        fl.setSpacing(0)

        # form heading
        form_title = QLabel("Sign in")
        form_title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #1d1d1f; border: none; letter-spacing: -0.3px;"
        )
        form_sub = QLabel("Enter your credentials to access the workspace.")
        form_sub.setStyleSheet(
            "font-size: 13px; color: #6e6e73; border: none; margin-top: 4px; margin-bottom: 24px;"
        )
        form_sub.setWordWrap(True)
        fl.addWidget(form_title)
        fl.addWidget(form_sub)

        # email
        self._label(fl, "Email or Username")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("admin@finauditpro.com")
        self.email_input.setFixedHeight(42)
        fl.addWidget(self.email_input)
        fl.addSpacing(14)

        # password
        self._label(fl, "Password")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setFixedHeight(42)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_login)
        fl.addWidget(self.password_input)
        fl.addSpacing(14)

        # options row
        opts = QHBoxLayout()
        self.chk = QCheckBox("Show password")
        self.chk.stateChanged.connect(self._toggle_pass)

        fp = QLabel("<a href='#' style='color:#007aff; text-decoration:none; font-size:12px; font-weight:500;'>Forgot password?</a>")
        fp.setOpenExternalLinks(False)
        fp.setStyleSheet("border:none; background:transparent;")
        fp.linkActivated.connect(self._forgot)

        opts.addWidget(self.chk)
        opts.addStretch()
        opts.addWidget(fp)
        fl.addLayout(opts)
        fl.addSpacing(20)

        # error label (hidden by default)
        self.err = QLabel()
        self.err.setStyleSheet(
            "background: #fee2e2; color: #dc2626; border: 1px solid #fecaca;"
            "border-radius: 8px; padding: 8px 12px; font-size: 12px; font-weight: 500;"
        )
        self.err.setWordWrap(True)
        self.err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.err.hide()
        fl.addWidget(self.err)

        # submit button
        self.btn = QPushButton("Continue")
        self.btn.setFixedHeight(42)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setObjectName("loginSubmitBtn")
        self.btn.clicked.connect(self.handle_login)
        fl.addWidget(self.btn)
        fl.addSpacing(20)

        # offline notice
        note = QLabel(
            "<span style='color:#64748b; font-size:11px;'>"
            "🔒  Fully offline · No data leaves your machine"
            "</span>"
        )
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("border:none; background:transparent;")
        fl.addWidget(note)

        # Default credential hint (shown only when initial default password is active)
        self.cred_hint = QLabel(
            "<span style='color:#94a3b8; font-size:10px;'>"
            "Default login: <b>admin@finauditpro.com</b> / <b>Admin@123</b>"
            "</span>"
        )
        self.cred_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cred_hint.setStyleSheet("border:none; background:transparent;")
        fl.addWidget(self.cred_hint)
        self._update_cred_hint_visibility()

        rl.addWidget(form)
        root.addWidget(left, stretch=4)
        root.addWidget(right_bg, stretch=5)

    # ── helpers ────────────────────────────────────────────────────────────────

    def _label(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #475569; border: none; margin-bottom: 6px;"
        )
        layout.addWidget(lbl)

    def _toggle_pass(self):
        mode = QLineEdit.EchoMode.Normal if self.chk.isChecked() else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)

    def _forgot(self, _=None):
        QMessageBox.information(
            self, "Password Recovery Instructions",
            "FinAuditPro is an air-gapped offline platform.\n\n"
            "To reset your administrator password via terminal, run:\n\n"
            "    python scripts/fix_admin.py --password <YourNewPassword>\n\n"
            "This administrative tool will update your account credentials securely."
        )

    def _update_cred_hint_visibility(self):
        """Show default credential hint only if default admin account uses Admin@123."""
        try:
            from security.auth import PasswordHasher
            from database.models import User
            with get_session() as session:
                user = session.query(User).filter_by(email="admin@finauditpro.com").first()
                if user and PasswordHasher.verify_password("Admin@123", user.password_hash):
                    self.cred_hint.show()
                    return
        except Exception:
            pass
        self.cred_hint.hide()

    # ── login logic ────────────────────────────────────────────────────────────

    def handle_login(self):
        email = self.email_input.text().strip()
        pwd = self.password_input.text()
        self.err.hide()

        if not email or not pwd:
            self._error("Email and password are required.")
            return

        self.btn.setEnabled(False)
        self.btn.setText("Signing in…")
        try:
            with get_session() as session:
                user_repo = UserRepository(session)
                user = AuthenticationService(user_repo).login(username=email, password=pwd)
                if user:
                    # Enforce password change if using default password
                    if pwd == "Admin@123":
                        from PySide6.QtWidgets import QInputDialog
                        new_pass, ok = QInputDialog.getText(
                            self,
                            "First-Time Login — Change Password",
                            "For security, please enter a new custom password for your administrator account:",
                            QLineEdit.EchoMode.Password
                        )
                        if ok and new_pass.strip():
                            if len(new_pass.strip()) < 8 or new_pass.strip() == "Admin@123":
                                self._error("Please choose a custom password with at least 8 characters.")
                                return
                            from security.auth import PasswordHasher
                            from database.models import User as UserModel
                            with get_session() as s2:
                                u = s2.query(UserModel).filter_by(id=user.id).first()
                                if u:
                                    u.password_hash = PasswordHasher.hash_password(new_pass.strip())
                                    s2.commit()
                            QMessageBox.information(self, "Password Updated", "Your password has been updated successfully!")
                            self._update_cred_hint_visibility()
                        else:
                            self._error("Password change is required on initial login.")
                            return

                    self.login_successful.emit(user)
                    return
                self._error("Incorrect email or password.")
        except Exception as e:
            self._error(f"Authentication failed: {str(e)}")
        finally:
            self.btn.setEnabled(True)
            self.btn.setText("Continue")


    def _error(self, msg: str):
        self.err.setText(msg)
        self.err.show()
        self.btn.setEnabled(True)
        self.btn.setText("Continue")
