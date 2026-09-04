"""Step-up Two-Factor Authentication (TOTP) verification modal dialog for statutory sign-offs and archival sealing."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.auth_service import AuthService


class StepUpTOTPDialog(QDialog):
    """Modern modal dialog verifying partner 2FA TOTP code for irreversible audit actions."""

    def __init__(
        self,
        parent: QWidget | None = None,
        action_title: str = "Statutory Sign-Off",
        action_description: str = "Enter the 6-digit code from your Authenticator app to authorize this statutory action.",
        auth_service: AuthService | None = None,
        user_session: UserSession | None = None,
    ) -> None:
        super().__init__(parent)
        self.action_title = action_title
        self.action_description = action_description
        self.auth_service = auth_service
        self.user_session = user_session
        self.is_authorized = False

        self.setWindowTitle("Two-Factor Authorization")
        self.setFixedSize(440, 360)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            QLabel {
                color: #0F172A;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: transparent;
            }
            QLineEdit#totpInput {
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px 14px;
                background: #F8FAFC;
                color: #0F172A;
                font-size: 22px;
                font-weight: 700;
                letter-spacing: 6px;
                qproperty-alignment: AlignCenter;
            }
            QLineEdit#totpInput:focus {
                border-color: #2563EB;
                background: #FFFFFF;
            }
            QPushButton#btnAuthorize {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                border-radius: 8px;
                padding: 10px 18px;
                border: none;
                min-height: 20px;
            }
            QPushButton#btnAuthorize:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btnCancel {
                background-color: #F1F5F9;
                color: #475569;
                font-size: 14px;
                font-weight: 500;
                border-radius: 8px;
                padding: 10px 18px;
                border: 1px solid #CBD5E1;
                min-height: 20px;
            }
            QPushButton#btnCancel:hover {
                background-color: #E2E8F0;
            }
        """)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header with Security Badge
        header_row = QHBoxLayout()
        icon_box = QLabel("🔒")
        icon_box.setFixedSize(36, 36)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet("background-color: #EFF6FF; border-radius: 8px; font-size: 18px;")
        header_row.addWidget(icon_box)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        lbl_title = QLabel(self.action_title)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        lbl_subtitle = QLabel("Step-Up Multi-Factor Attestation")
        lbl_subtitle.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")
        title_v.addWidget(lbl_title)
        title_v.addWidget(lbl_subtitle)
        header_row.addLayout(title_v)
        header_row.addStretch()
        layout.addLayout(header_row)

        desc_card = QFrame()
        desc_card.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px;"
        )
        dl = QVBoxLayout(desc_card)
        dl.setContentsMargins(4, 4, 4, 4)
        lbl_desc = QLabel(self.action_description)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 12px; color: #475569; line-height: 1.4;")
        dl.addWidget(lbl_desc)
        layout.addWidget(desc_card)

        self.input_totp = QLineEdit()
        self.input_totp.setObjectName("totpInput")
        self.input_totp.setPlaceholderText("000000")
        self.input_totp.setMaxLength(6)
        self.input_totp.returnPressed.connect(self._handle_verify)
        layout.addWidget(self.input_totp)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color: #DC2626; font-size: 12px; font-weight: 500;")
        self.lbl_error.setVisible(False)
        layout.addWidget(self.lbl_error)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        self.btn_auth = QPushButton("Authorize Action")
        self.btn_auth.setObjectName("btnAuthorize")
        self.btn_auth.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auth.clicked.connect(self._handle_verify)

        btn_row.addWidget(btn_cancel, 1)
        btn_row.addWidget(self.btn_auth, 2)
        layout.addLayout(btn_row)

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        self.input_totp.clear()
        self.lbl_error.setVisible(False)
        self.input_totp.setFocus()

    def _handle_verify(self) -> None:
        token = self.input_totp.text().strip()
        if not token or len(token) != 6 or not token.isdigit():
            self.lbl_error.setText("Please enter a valid 6-digit verification code.")
            self.lbl_error.setVisible(True)
            self.input_totp.setFocus()
            return

        # If user has TOTP configured in auth_service, verify strictly
        if (
            self.auth_service
            and self.user_session
            and hasattr(self.user_session, "user_id")
            and not self.auth_service.verify_user_totp(self.user_session.user_id, token)
        ):
            self.lbl_error.setText("Invalid or expired 6-digit code. Please try again.")
            self.lbl_error.setVisible(True)
            self.input_totp.selectAll()
            self.input_totp.setFocus()
            return

        self.is_authorized = True
        self.accept()
