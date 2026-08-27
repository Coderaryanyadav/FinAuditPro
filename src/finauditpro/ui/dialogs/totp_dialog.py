import qrcode
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
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


class TOTPDialog(QDialog):
    """Dialog to enable or disable Two-Factor Authentication (TOTP)."""

    def __init__(
        self,
        parent: QWidget | None = None,
        auth_service: AuthService | None = None,
        user_session: UserSession | None = None,
    ) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.user_session = user_session
        self.secret: str | None = None

        self.setWindowTitle("Two-Factor Authentication (2FA)")
        self.setFixedSize(500, 500)
        self.setStyleSheet("background-color: #FFFFFF;")

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Secure Your Account with 2FA")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        desc = QLabel(
            "Two-Factor Authentication adds an extra layer of security. "
            "Use an authenticator app (like Google Authenticator or Authy) to scan the QR code."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #475569;")
        layout.addWidget(desc)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.qr_label)

        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Enter 6-digit code")
        self.input_token.setMaxLength(6)
        self.input_token.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_token.setStyleSheet("font-size: 18px; padding: 10px;")
        layout.addWidget(self.input_token)

        btn_row = QHBoxLayout()
        self.btn_action = QPushButton("Verify && Enable 2FA")
        self.btn_action.setObjectName("primaryButton")
        self.btn_action.clicked.connect(self._on_enable_clicked)

        self.btn_disable = QPushButton("Disable 2FA")
        self.btn_disable.setStyleSheet("color: #DC2626; border: 1px solid #DC2626;")
        self.btn_disable.clicked.connect(self._on_disable_clicked)

        btn_row.addWidget(self.btn_action)
        btn_row.addWidget(self.btn_disable)
        layout.addLayout(btn_row)

        self._setup_totp()

    def _setup_totp(self) -> None:
        if not self.auth_service or not self.user_session:
            return

        if self.auth_service.is_totp_enabled_for_user(self.user_session.user_id):
            self.btn_action.setEnabled(False)
            self.btn_disable.setEnabled(True)
            self.input_token.setEnabled(False)
            self.qr_label.setText("2FA is currently ENABLED for this account.")
            self.qr_label.setStyleSheet("color: #16A34A; font-weight: bold;")
            return

        self.btn_disable.setEnabled(False)
        self.secret = self.auth_service.generate_totp_secret()
        uri = self.auth_service.get_totp_uri(self.secret, self.user_session.username)

        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to QPixmap
        img = img.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qim = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qim)
        self.qr_label.setPixmap(pix)

    def _on_enable_clicked(self) -> None:
        if not self.auth_service or not self.user_session or not self.secret:
            return

        token = self.input_token.text().strip()
        if not token or len(token) != 6:
            QMessageBox.warning(self, "Invalid Token", "Please enter a valid 6-digit token.")
            return

        try:
            self.auth_service.enable_totp(self.user_session.user_id, self.secret, token)
            QMessageBox.information(self, "2FA Enabled", "Two-Factor Authentication is now enabled.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Verification Failed", str(e))

    def _on_disable_clicked(self) -> None:
        if not self.auth_service or not self.user_session:
            return

        reply = QMessageBox.question(
            self, "Disable 2FA",
            "Are you sure you want to disable Two-Factor Authentication? This reduces account security.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.auth_service.disable_totp(self.user_session.user_id)
                QMessageBox.information(self, "2FA Disabled", "Two-Factor Authentication has been disabled.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
