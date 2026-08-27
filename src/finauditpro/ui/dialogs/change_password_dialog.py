"""Change Password / First-Login Mandatory Password Reset Dialog."""

from PySide6.QtCore import Qt
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


class ChangePasswordDialog(QDialog):
    """Modal dialog prompting the user to set a secure master password."""

    def __init__(
        self,
        parent: QWidget | None = None,
        auth_service: AuthService | None = None,
        user_session: UserSession | None = None,
        is_forced: bool = True,
    ) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.user_session = user_session
        self.is_forced = is_forced
        self.updated_session: UserSession | None = None

        self.setWindowTitle("Security Requirement: Account Setup")
        self.setFixedSize(520, 520)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Header Badge & Title
        header_frame = QFrame()
        hl = QVBoxLayout(header_frame)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)

        badge = QLabel("MANDATORY SECURITY SETUP")
        badge.setStyleSheet("""
            font-size: 11px; font-weight: 700; color: #DC2626;
            background: #FEF2F2; border: 1px solid #FEE2E2;
            border-radius: 4px; padding: 4px 8px; max-width: 220px;
        """)
        hl.addWidget(badge)

        title = QLabel("Set Up Auditor Credentials" if self.is_forced else "Update Credentials")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        hl.addWidget(title)

        desc_text = (
            "Set your personal auditor email address and a secure master password "
            "to replace default setup credentials before accessing the audit workspace."
            if self.is_forced
            else "Update your account email and password to maintain audit system security."
        )
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #64748B; line-height: 1.4;")
        hl.addWidget(desc)
        layout.addWidget(header_frame)

        # Form fields
        form_frame = QFrame()
        fl = QVBoxLayout(form_frame)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(10)

        field_qss = """
            QLineEdit {
                border: 1.5px solid #CBD5E1; border-radius: 6px;
                padding: 8px 12px; font-size: 13px; color: #0F172A; background: #FFFFFF;
            }
            QLineEdit:focus { border-color: #2563EB; background: #FFFFFF; }
            QLineEdit::placeholder { color: #94A3B8; }
        """

        lbl_email = QLabel("Auditor Email Address")
        lbl_email.setStyleSheet("font-size: 12px; font-weight: 600; color: #1E293B;")
        self.input_email = QLineEdit()
        current_email = self.user_session.username if self.user_session else "admin@finauditpro.com"
        self.input_email.setText(current_email)
        self.input_email.setPlaceholderText("e.g. ca.sharma@firm.com")
        self.input_email.setStyleSheet(field_qss)
        fl.addWidget(lbl_email)
        fl.addWidget(self.input_email)

        lbl_new = QLabel("New Master Password")
        lbl_new.setStyleSheet("font-size: 12px; font-weight: 600; color: #1E293B;")
        self.input_new = QLineEdit()
        self.input_new.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_new.setPlaceholderText("Minimum 8 characters (letters + numbers/symbols)")
        self.input_new.setStyleSheet(field_qss)
        toggle_new = QAction("Show", self.input_new)
        self.input_new.addAction(toggle_new, QLineEdit.ActionPosition.TrailingPosition)

        def _toggle_new_pwd() -> None:
            if self.input_new.echoMode() == QLineEdit.EchoMode.Password:
                self.input_new.setEchoMode(QLineEdit.EchoMode.Normal)
                toggle_new.setText("Hide")
            else:
                self.input_new.setEchoMode(QLineEdit.EchoMode.Password)
                toggle_new.setText("Show")

        toggle_new.triggered.connect(_toggle_new_pwd)

        fl.addWidget(lbl_new)
        fl.addWidget(self.input_new)

        lbl_confirm = QLabel("Confirm New Password")
        lbl_confirm.setStyleSheet("font-size: 12px; font-weight: 600; color: #1E293B;")
        self.input_confirm = QLineEdit()
        self.input_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirm.setPlaceholderText("Re-type new password to confirm")
        self.input_confirm.setStyleSheet(field_qss)
        toggle_confirm = QAction("Show", self.input_confirm)
        self.input_confirm.addAction(toggle_confirm, QLineEdit.ActionPosition.TrailingPosition)

        def _toggle_confirm_pwd() -> None:
            if self.input_confirm.echoMode() == QLineEdit.EchoMode.Password:
                self.input_confirm.setEchoMode(QLineEdit.EchoMode.Normal)
                toggle_confirm.setText("Hide")
            else:
                self.input_confirm.setEchoMode(QLineEdit.EchoMode.Password)
                toggle_confirm.setText("Show")

        toggle_confirm.triggered.connect(_toggle_confirm_pwd)

        fl.addWidget(lbl_confirm)
        fl.addWidget(self.input_confirm)

        layout.addWidget(form_frame)

        # Requirements Note
        req = QLabel("Min. 8 characters  •  Letters & numbers/symbols  •  Cannot be Admin@123")
        req.setStyleSheet("font-size: 11px; font-weight: 500; color: #64748B;")
        layout.addWidget(req)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        if not self.is_forced:
            btn_cancel = QPushButton("Cancel")
            btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_cancel.setStyleSheet("""
                QPushButton {
                    background: #F1F5F9; color: #475569; font-size: 13px; font-weight: 600;
                    border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 16px;
                }
                QPushButton:hover { background: #E2E8F0; }
            """)
            btn_cancel.clicked.connect(self.reject)
            btn_layout.addWidget(btn_cancel)

        self.btn_save = QPushButton("Save Credentials && Access Workspace →")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #2563EB; color: #FFFFFF; font-size: 13px; font-weight: 600;
                border: 1px solid transparent; border-radius: 6px; padding: 10px 20px;
            }
            QPushButton:hover { background: #1D4ED8; }
            QPushButton:pressed { background: #1E40AF; }
        """)
        self.btn_save.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(self.btn_save, 1)

        layout.addLayout(btn_layout)

    def _on_save_clicked(self) -> None:
        email = self.input_email.text().strip()
        p1 = self.input_new.text()
        p2 = self.input_confirm.text()

        if not email or "@" not in email:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address.")
            return

        if not p1 or not p2:
            QMessageBox.warning(self, "Validation Error", "Please enter and confirm your new password.")
            return

        if p1 != p2:
            QMessageBox.warning(self, "Validation Error", "New passwords do not match. Please re-enter.")
            return

        if not self.auth_service or not self.user_session:
            QMessageBox.critical(self, "Error", "Authentication service context is missing.")
            return

        try:
            new_session = self.auth_service.force_setup_credentials(
                self.user_session.user_id, email, p1
            )
            self.updated_session = new_session
            QMessageBox.information(
                self,
                "Setup Completed",
                f"Auditor credentials for '{new_session.username}' successfully configured. Default credentials replaced.",
            )
            self.accept()
        except ValidationError as ex:
            QMessageBox.warning(self, "Validation Error", str(ex))
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to update credentials: {ex}")
