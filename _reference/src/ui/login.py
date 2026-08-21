"""
FinAuditPro — Login Screen
Design language: Slate Dark — deep slate navy with sky-blue accents.
Left: brand panel with clear typography and trust indicators.
Right: enterprise login form with crisp dark card, glowing inputs and primary CTA.
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
        border: 1.5px solid #D1D5DB;
        border-radius: 6px;
        padding: 10px 14px;
        background-color: #FFFFFF;
        font-size: 13px;
        color: #111827;
    }
    QLineEdit:focus {
        border-color: #2563EB;
        background-color: #FFFFFF;
    }
    QLineEdit:hover { border-color: #9CA3AF; }
"""

_COMBO = """
    QComboBox {
        border: 1.5px solid #D1D5DB;
        border-radius: 6px;
        padding: 10px 14px;
        background-color: #FFFFFF;
        font-size: 13px;
        color: #111827;
        font-weight: 400;
    }
    QComboBox:focus  { border-color: #2563EB; background-color: #FFFFFF; }
    QComboBox:hover  { border-color: #9CA3AF; }
    QComboBox::drop-down { border: none; width: 26px; }
    QComboBox QAbstractItemView {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        color: #111827;
        selection-background-color: #2563EB;
        selection-color: #FFFFFF;
        outline: none;
        padding: 4px;
    }
"""


class LoginWindow(QWidget):
    """Enterprise Auditor Login Window — Sky Blue & White Theme."""
    login_successful = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinAuditPro — Statutory Audit Platform")
        self.resize(1080, 680)
        self.setObjectName("appBg")
        self.setMinimumSize(780, 560)
        self.setStyleSheet("background-color: #F7F8FA;")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT: brand panel ────────────────────────────────────────
        left = QFrame()
        left.setObjectName("loginHeroPanel")
        left.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f172a, stop:1 #1e293b);"
            "border-right: 1px solid #1e293b;"
        )
        ll = QVBoxLayout(left)
        ll.setContentsMargins(56, 60, 56, 48)
        ll.setSpacing(0)

        # logo mark
        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(34, 34)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #2563EB; color: #fff; border-radius: 8px;"
            "font-size: 13px; font-weight: 700; border: none;"
        )
        logo_name = QLabel("FinAuditPro")
        logo_name.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #ffffff; border: none; background: transparent; background-color: transparent; margin-left: 10px;"
        )
        logo_row.addWidget(logo_box)
        logo_row.addWidget(logo_name)
        logo_row.addStretch()
        ll.addLayout(logo_row)
        ll.addStretch(1)

        # headline
        h1 = QLabel("Built for\nstatutory auditors.")
        h1.setStyleSheet(
            "font-size: 36px; font-weight: 700; color: #ffffff; border: none; background: transparent; background-color: transparent;"
            "line-height: 1.2; letter-spacing: -0.8px;"
        )
        h1.setWordWrap(True)
        ll.addWidget(h1)
        ll.addSpacing(16)

        sub = QLabel(
            "Automated working papers, AI-assisted findings,\nGST reconciliation — all offline, all secure."
        )
        sub.setStyleSheet("font-size: 14px; color: #94a3b8; border: none; background: transparent; background-color: transparent; line-height: 1.5;")
        sub.setWordWrap(True)
        ll.addWidget(sub)
        ll.addStretch(2)

        # feature list
        features = [
            "100% air-gapped — no cloud dependency",
            "SA 230 compliant electronic working papers",
            "ICAI statutory audit workflows (CARO 2020)",
        ]
        for f in features:
            row = QHBoxLayout()
            dot = QLabel("✓")
            dot.setStyleSheet("font-size: 13px; color: #38BDF8; border: none; background: transparent; font-weight: 600;")
            dot.setFixedWidth(20)
            tx = QLabel(f)
            tx.setStyleSheet("font-size: 13px; color: #CBD5E1; border: none; background: transparent; font-weight: 400;")
            row.addWidget(dot)
            row.addWidget(tx)
            row.addStretch()
            ll.addLayout(row)
            ll.addSpacing(8)

        ll.addStretch(3)

        # version footer
        ver = QLabel("Enterprise v2.4.0 · Local deployment")
        ver.setStyleSheet("font-size: 11px; color: #64748b; border: none; background: transparent; background-color: transparent;")
        ll.addWidget(ver)

        # ── RIGHT: form ───────────────────────────────────────────────
        right_bg = QWidget()
        right_bg.setObjectName("loginRightBg")
        right_bg.setStyleSheet("background-color: #F7F8FA;")
        rl = QVBoxLayout(right_bg)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.setContentsMargins(52, 40, 52, 40)

        form = QFrame()
        form.setObjectName("loginFormContainer")
        form.setFixedWidth(380)
        form.setStyleSheet(
            "QFrame#loginFormContainer {"
            "  background-color: #FFFFFF;"
            "  border: 1px solid #E5E7EB;"
            "  border-radius: 12px;"
            "}"
        )
        apply_shadow(form, blur=32, dy=12, alpha=16)

        fl = QVBoxLayout(form)
        fl.setContentsMargins(36, 36, 36, 36)
        fl.setSpacing(0)

        # form heading
        form_title = QLabel("Sign in to FinAuditPro")
        form_title.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #111827; border: none; background: transparent; letter-spacing: -0.2px;"
        )
        form_sub = QLabel("Enter your credentials to access the workspace.")
        form_sub.setStyleSheet(
            "font-size: 13px; color: #64748b; border: none; background: transparent; background-color: transparent; margin-top: 4px; margin-bottom: 24px;"
        )
        form_sub.setWordWrap(True)
        fl.addWidget(form_title)
        fl.addWidget(form_sub)

        # email
        self._label(fl, "Email or Username")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("admin@finauditpro.com")
        self.email_input.setFixedHeight(42)
        self.email_input.setStyleSheet(_INPUT)
        fl.addWidget(self.email_input)
        fl.addSpacing(14)

        # password
        self._label(fl, "Password")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setFixedHeight(42)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(_INPUT)
        self.password_input.returnPressed.connect(self.handle_login)
        fl.addWidget(self.password_input)

        # Item 20: Caps lock warning label
        self.caps_lbl = QLabel("⚠️ Caps Lock is ON")
        self.caps_lbl.setStyleSheet("color: #d97706; font-size: 11px; font-weight: 600; margin-top: 2px; border: none; background: transparent;")
        self.caps_lbl.hide()
        fl.addWidget(self.caps_lbl)

        fl.addSpacing(10)

        # options row
        opts = QHBoxLayout()
        self.chk = QCheckBox("Show password")
        self.chk.setStyleSheet(
            "QCheckBox { font-size: 12px; color: #475569; border: none; background: transparent; spacing: 6px; }"
            "QCheckBox::indicator { width: 15px; height: 15px; border-radius: 4px;"
            "  border: 1.5px solid #cbd5e1; background: #ffffff; }"
            "QCheckBox::indicator:checked { background: #0284c7; border-color: #0284c7; }"
        )
        self.chk.stateChanged.connect(self._toggle_pass)

        fp = QLabel("<a href='#' style='color:#0284c7; text-decoration:none; font-size:12px; font-weight:500;'>Forgot password?</a>")
        fp.setOpenExternalLinks(False)
        fp.setStyleSheet("border:none; background:transparent; background-color:transparent;")
        fp.linkActivated.connect(self._forgot)

        opts.addWidget(self.chk)
        opts.addStretch()
        opts.addWidget(fp)
        fl.addLayout(opts)
        fl.addSpacing(20)

        # error label (hidden by default)
        self.err = QLabel()
        self.err.setStyleSheet(
            "background: rgba(244, 63, 94, 0.1); color: #dc2626; border: 1px solid rgba(220, 38, 38, 0.3);"
            "border-radius: 8px; padding: 8px 12px; font-size: 12px; font-weight: 500;"
        )
        self.err.setWordWrap(True)
        self.err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.err.hide()
        fl.addWidget(self.err)

        # submit button
        self.btn = QPushButton("Continue")
        self.btn.setFixedHeight(44)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setObjectName("loginSubmitBtn")
        self.btn.setStyleSheet("""
            QPushButton#loginSubmitBtn {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
                border-radius: 8px;
                border: none;
                letter-spacing: 0.3px;
            }
            QPushButton#loginSubmitBtn:hover {
                background-color: #0369a1;
            }
            QPushButton#loginSubmitBtn:pressed {
                background-color: #075985;
            }
            QPushButton#loginSubmitBtn:disabled { background: #e2e8f0; color: #94a3b8; border: none; }
        """)
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
        note.setStyleSheet("border:none; background:transparent; background-color:transparent;")
        fl.addWidget(note)

        # Default credential hint (shown only when initial default password is active)
        self.cred_hint = QLabel(
            "<span style='color:#64748b; font-size:10px;'>"
            "Default login: <b>admin@finauditpro.com</b> / <b>Admin@123</b>"
            "</span>"
        )
        self.cred_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cred_hint.setStyleSheet("border:none; background:transparent; background-color:transparent;")
        fl.addWidget(self.cred_hint)
        self._update_cred_hint_visibility()

        rl.addWidget(form)
        root.addWidget(left, stretch=4)
        root.addWidget(right_bg, stretch=5)

    # ── helpers ────────────────────────────────────────────────────────────────

    def _label(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #475569; border: none; background: transparent; background-color: transparent; margin-bottom: 6px;"
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
