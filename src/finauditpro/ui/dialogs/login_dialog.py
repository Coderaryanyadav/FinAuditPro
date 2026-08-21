"""
FinAuditPro Enterprise — Auditor Login Dialog & First-Time Password Flow
Split-view authentication window matching enterprise design standards.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoginDialog(QDialog):
    """Enterprise Auditor Login Window — Split Navy & White Surface Design."""

    login_successful = Signal(str, str)  # username, role

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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
            "font-size: 18px; font-weight: 700; color: #ffffff; border: none; margin-left: 10px;"
        )
        logo_row.addWidget(logo_box)
        logo_row.addWidget(logo_name)
        logo_row.addStretch()
        ll.addLayout(logo_row)
        ll.addStretch(1)

        # Headline
        h1 = QLabel("Built for\nstatutory auditors.")
        h1.setStyleSheet(
            "font-size: 34px; font-weight: 800; color: #ffffff; border: none;"
            "line-height: 1.2; letter-spacing: -0.6px;"
        )
        h1.setWordWrap(True)
        ll.addWidget(h1)
        ll.addSpacing(14)

        sub = QLabel(
            "Automated working papers, AI-assisted analytics,\nCARO 2020 & GST reconciliation — all offline, all local."
        )
        sub.setStyleSheet("font-size: 13px; color: #94a3b8; border: none; line-height: 1.5;")
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
            dot = QLabel("✓")
            dot.setStyleSheet("font-size: 13px; color: #38BDF8; font-weight: 700;")
            dot.setFixedWidth(20)
            tx = QLabel(f)
            tx.setStyleSheet("font-size: 13px; color: #CBD5E1; font-weight: 400;")
            row.addWidget(dot)
            row.addWidget(tx)
            row.addStretch()
            ll.addLayout(row)
            ll.addSpacing(8)

        ll.addStretch(3)

        ver = QLabel("Enterprise v2.4.0 · Local deployment")
        ver.setStyleSheet("font-size: 11px; color: #64748b;")
        ll.addWidget(ver)

        # ── RIGHT: Form ───────────────────────────────────────────────
        right_bg = QWidget()
        right_bg.setStyleSheet("background-color: #F7F8FA;")
        rl = QVBoxLayout(right_bg)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form = QFrame()
        form.setFixedWidth(380)
        form.setStyleSheet(
            "background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;"
        )

        fl = QVBoxLayout(form)
        fl.setContentsMargins(32, 32, 32, 32)
        fl.setSpacing(0)

        form_title = QLabel("Sign in to FinAuditPro")
        form_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #111827;")
        form_sub = QLabel("Enter your credentials to access the workspace.")
        form_sub.setStyleSheet("font-size: 12px; color: #6B7280; margin-top: 4px;")

        fl.addWidget(form_title)
        fl.addWidget(form_sub)
        fl.addSpacing(24)

        # Inputs
        lbl_e = QLabel("Email / Username")
        lbl_e.setStyleSheet("font-size: 11px; font-weight: 600; color: #374151; margin-bottom: 4px;")
        self.input_user = QLineEdit("admin@finauditpro.com")
        self.input_user.setStyleSheet(
            "QLineEdit { border: 1px solid #D1D5DB; border-radius: 6px; padding: 9px 12px; background: #FFFFFF; color: #111827; font-size: 13px; }"
            "QLineEdit:focus { border-color: #007AFF; }"
        )

        lbl_p = QLabel("Password")
        lbl_p.setStyleSheet("font-size: 11px; font-weight: 600; color: #374151; margin-top: 14px; margin-bottom: 4px;")
        self.input_pass = QLineEdit("Admin@123")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setStyleSheet(
            "QLineEdit { border: 1px solid #D1D5DB; border-radius: 6px; padding: 9px 12px; background: #FFFFFF; color: #111827; font-size: 13px; }"
            "QLineEdit:focus { border-color: #007AFF; }"
        )

        fl.addWidget(lbl_e)
        fl.addWidget(self.input_user)
        fl.addWidget(lbl_p)
        fl.addWidget(self.input_pass)
        fl.addSpacing(20)

        # Submit CTA
        self.btn_submit = QPushButton("Sign In")
        self.btn_submit.setFixedHeight(40)
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.setStyleSheet(
            "QPushButton { background-color: #007AFF; color: #FFFFFF; font-size: 13px; font-weight: 600; border-radius: 6px; border: none; }"
            "QPushButton:hover { background-color: #0062CC; }"
        )
        self.btn_submit.clicked.connect(self._handle_login)

        fl.addWidget(self.btn_submit)
        fl.addSpacing(16)

        hint = QLabel("🔒 Fully offline · No data leaves your machine\nDefault login: admin@finauditpro.com / Admin@123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: 11px; color: #64748b; line-height: 1.4;")
        fl.addWidget(hint)

        rl.addWidget(form)

        root.addWidget(left, 45)
        root.addWidget(right_bg, 55)

    def _handle_login(self) -> None:
        user = self.input_user.text().strip()
        pwd = self.input_pass.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, "Validation Error", "Please enter both username and password.")
            return

        if pwd == "Admin@123":
            new_pwd, ok = QInputDialog.getText(
                self,
                "First-Time Login — Change Password",
                "For security, please enter a new custom password for your administrator account:",
                QLineEdit.EchoMode.Password,
            )
            if not ok or not new_pwd:
                return

        self.login_successful.emit(user, "Administrator")
        self.accept()
