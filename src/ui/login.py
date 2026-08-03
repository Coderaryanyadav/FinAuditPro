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
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 14px;
        background-color: #ffffff;
        font-size: 13px;
        color: #0f172a;
    }
    QLineEdit:focus {
        border-color: #0284c7;
        background-color: #ffffff;
    }
    QLineEdit:hover { border-color: #94a3b8; }
"""

_COMBO = """
    QComboBox {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 14px;
        background-color: #ffffff;
        font-size: 13px;
        color: #0f172a;
        font-weight: 400;
    }
    QComboBox:focus  { border-color: #0284c7; }
    QComboBox:hover  { border-color: #94a3b8; }
    QComboBox::drop-down { border: none; width: 26px; }
    QComboBox QAbstractItemView {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #0f172a;
        selection-background-color: #e0f2fe;
        selection-color: #0284c7;
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
        left.setStyleSheet("QFrame { background-color: #f1f5f9; border-right: 1px solid #e2e8f0; }")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(56, 60, 56, 48)
        ll.setSpacing(0)

        # logo mark
        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(34, 34)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #0284c7; color: #fff; border-radius: 8px;"
            "font-size: 13px; font-weight: 800; border: none;"
        )
        logo_name = QLabel("FinAuditPro")
        logo_name.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #0f172a; border: none; margin-left: 10px;"
        )
        logo_row.addWidget(logo_box)
        logo_row.addWidget(logo_name)
        logo_row.addStretch()
        ll.addLayout(logo_row)
        ll.addStretch(1)

        # headline
        h1 = QLabel("Built for\nstatutory auditors.")
        h1.setStyleSheet(
            "font-size: 36px; font-weight: 700; color: #0f172a; border: none; line-height: 1.2; letter-spacing: -0.8px;"
        )
        h1.setWordWrap(True)
        ll.addWidget(h1)
        ll.addSpacing(16)

        sub = QLabel(
            "Automated working papers, AI-assisted findings,\nGST reconciliation — all offline, all secure."
        )
        sub.setStyleSheet("font-size: 14px; color: #475569; border: none; line-height: 1.5;")
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
            dot.setStyleSheet("font-size: 13px; color: #0284c7; border: none; font-weight: 700;")
            dot.setFixedWidth(20)
            tx = QLabel(f)
            tx.setStyleSheet("font-size: 13px; color: #334155; border: none; font-weight: 500;")
            row.addWidget(dot)
            row.addWidget(tx)
            row.addStretch()
            ll.addLayout(row)
            ll.addSpacing(10)

        ll.addStretch(3)

        # version footer
        ver = QLabel("Enterprise v2.4.0 · Local deployment")
        ver.setStyleSheet("font-size: 11px; color: #94a3b8; border: none;")
        ll.addWidget(ver)

        # ── RIGHT: form ───────────────────────────────────────────────
        right_bg = QWidget()
        right_bg.setObjectName("loginRightBg")
        right_bg.setStyleSheet("background-color: #f8fafc;")
        rl = QVBoxLayout(right_bg)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.setContentsMargins(52, 40, 52, 40)

        form = QFrame()
        form.setObjectName("loginFormContainer")
        form.setFixedWidth(400)
        form.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 14px;
                border: 1px solid #e2e8f0;
            }
        """)
        apply_shadow(form, blur=24, dy=8, alpha=30)

        fl = QVBoxLayout(form)
        fl.setContentsMargins(36, 36, 36, 36)
        fl.setSpacing(0)

        # form heading
        form_title = QLabel("Sign in")
        form_title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #0f172a; border: none; letter-spacing: -0.3px;"
        )
        form_sub = QLabel("Enter your credentials to access the workspace.")
        form_sub.setStyleSheet(
            "font-size: 13px; color: #64748b; border: none; margin-top: 4px; margin-bottom: 24px;"
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
        fl.addSpacing(14)

        # role
        self._label(fl, "Role")
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Audit Partner — Full access",
            "Senior Auditor — Reviewer",
            "Junior Assistant — Preparer",
        ])
        self.role_combo.setFixedHeight(42)
        self.role_combo.setStyleSheet(_COMBO)
        fl.addWidget(self.role_combo)
        fl.addSpacing(12)

        # options row
        opts = QHBoxLayout()
        self.chk = QCheckBox("Show password")
        self.chk.setStyleSheet("""
            QCheckBox { border: none; background: transparent; color: #475569; font-size: 12px; spacing: 6px; }
            QCheckBox::indicator {
                width: 15px; height: 15px; border-radius: 4px;
                border: 1px solid #cbd5e1; background: #ffffff;
            }
            QCheckBox::indicator:checked { background: #0284c7; border-color: #0284c7; }
        """)
        self.chk.stateChanged.connect(self._toggle_pass)

        fp = QLabel("<a href='#' style='color:#0284c7; text-decoration:none; font-size:12px; font-weight:500;'>Forgot password?</a>")
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
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
            QPushButton:pressed { background-color: #075985; }
            QPushButton:disabled { background-color: #f1f5f9; color: #cbd5e1; }
        """)
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

        # Default credential hint (shown on fresh install)
        cred_hint = QLabel(
            "<span style='color:#94a3b8; font-size:10px;'>"
            "Default login: <b>admin@finauditpro.com</b> / <b>Admin@123</b>"
            "</span>"
        )
        cred_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cred_hint.setStyleSheet("border:none; background:transparent;")
        fl.addWidget(cred_hint)

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
            self, "Password Reset",
            "FinAuditPro is fully air-gapped.\n"
            "Contact your administrator to reset passwords via the admin CLI."
        )

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
                # Pass 'username' argument to login() which handles username or email
                user = AuthenticationService(user_repo).login(username=email, password=pwd)
                if user:
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
