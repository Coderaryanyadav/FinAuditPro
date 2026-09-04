"""Two-Factor Authentication (TOTP) configuration dialog with QR code and copyable secret key."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
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


class TOTPDialog(QDialog):
    """Dialog to enable or disable Two-Factor Authentication (TOTP) with QR code & secret key fallback."""

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
        self.setFixedSize(520, 560)
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
                font-size: 20px;
                font-weight: 700;
                letter-spacing: 4px;
                qproperty-alignment: AlignCenter;
            }
            QLineEdit#totpInput:focus {
                border-color: #2563EB;
                background: #FFFFFF;
            }
            QPushButton#primaryButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 9px 18px;
                border: none;
            }
            QPushButton#primaryButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btnCopyKey {
                background-color: #F1F5F9;
                color: #334155;
                font-size: 11px;
                font-weight: 600;
                border-radius: 6px;
                padding: 4px 10px;
                border: 1px solid #CBD5E1;
            }
            QPushButton#btnCopyKey:hover {
                background-color: #E2E8F0;
            }
        """)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Two-Factor Authentication (2FA)")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        desc = QLabel(
            "Scan the QR code or enter the secret key below into your Authenticator app (Google Authenticator, Apple Passwords, Microsoft Authenticator, or Authy)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #64748B; line-height: 1.4;")
        layout.addWidget(desc)

        # QR Code Container / Status
        self.qr_container = QFrame()
        self.qr_container.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px;"
        )
        qr_layout = QVBoxLayout(self.qr_container)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(self.qr_label)

        # Secret Key Row with Copy button
        self.key_card = QFrame()
        self.key_card.setStyleSheet(
            "background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px;"
        )
        key_layout = QHBoxLayout(self.key_card)
        key_layout.setContentsMargins(4, 2, 4, 2)

        self.lbl_secret_key = QLabel("Secret Key: ----")
        self.lbl_secret_key.setStyleSheet(
            "font-family: monospace; font-size: 13px; font-weight: 700; color: #1E293B;"
        )
        key_layout.addWidget(self.lbl_secret_key)
        key_layout.addStretch()

        btn_copy = QPushButton("📋 Copy Key")
        btn_copy.setObjectName("btnCopyKey")
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.clicked.connect(self._copy_secret_key)
        key_layout.addWidget(btn_copy)

        qr_layout.addWidget(self.key_card)
        layout.addWidget(self.qr_container)

        self.input_token = QLineEdit()
        self.input_token.setObjectName("totpInput")
        self.input_token.setPlaceholderText("000000")
        self.input_token.setMaxLength(6)
        layout.addWidget(self.input_token)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color: #DC2626; font-size: 12px; font-weight: 500;")
        self.lbl_error.setVisible(False)
        layout.addWidget(self.lbl_error)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_disable = QPushButton("Disable 2FA")
        self.btn_disable.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_disable.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2; color: #DC2626; font-size: 13px; font-weight: 600;
                border-radius: 8px; padding: 9px 18px; border: 1px solid #FCA5A5;
            }
            QPushButton:hover { background-color: #FEE2E2; }
        """)
        self.btn_disable.clicked.connect(self._on_disable_clicked)

        self.btn_action = QPushButton("Verify & Enable 2FA")
        self.btn_action.setObjectName("primaryButton")
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self._on_enable_clicked)

        btn_row.addWidget(self.btn_disable)
        btn_row.addWidget(self.btn_action)
        layout.addLayout(btn_row)

        self._setup_totp()

    def _copy_secret_key(self) -> None:
        if self.secret:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.secret)
            QMessageBox.information(
                self,
                "Copied",
                "Secret Key copied to clipboard!\nPaste it into your Authenticator app.",
            )

    def _setup_totp(self) -> None:
        if not self.auth_service or not self.user_session:
            return

        if self.auth_service.is_totp_enabled_for_user(self.user_session.user_id):
            self.btn_action.setEnabled(False)
            self.btn_disable.setEnabled(True)
            self.input_token.setEnabled(False)
            self.key_card.setVisible(False)
            self.qr_label.setText("✓ 2FA is currently ENABLED and active for this account.")
            self.qr_label.setStyleSheet(
                "color: #16A34A; font-size: 14px; font-weight: bold; padding: 24px;"
            )
            return

        self.btn_disable.setEnabled(False)
        self.secret = self.auth_service.generate_totp_secret()
        formatted_secret = " ".join([self.secret[i : i + 4] for i in range(0, len(self.secret), 4)])
        self.lbl_secret_key.setText(f"Key: {formatted_secret}")

        uri = self.auth_service.get_totp_uri(self.secret, self.user_session.username)

        # Attempt QR code generation with graceful text fallback
        qr_rendered = False
        try:
            import qrcode  # type: ignore[import-untyped]

            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qim = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
            pix = QPixmap.fromImage(qim)
            self.qr_label.setPixmap(pix)
            qr_rendered = True
        except Exception:
            qr_rendered = False

        if not qr_rendered:
            self.qr_label.setText(
                "🔑 Manual Key Setup Mode\nEnter the Secret Key below into your Authenticator App:"
            )
            self.qr_label.setStyleSheet(
                "color: #334155; font-size: 13px; font-weight: 600; padding: 12px;"
            )

    def _on_enable_clicked(self) -> None:
        if not self.auth_service or not self.user_session or not self.secret:
            return

        token = self.input_token.text().strip()
        if not token or len(token) != 6 or not token.isdigit():
            self.lbl_error.setText(
                "Please enter the 6-digit verification code from your Authenticator app."
            )
            self.lbl_error.setVisible(True)
            self.input_token.setFocus()
            return

        try:
            self.auth_service.enable_totp(self.user_session.user_id, self.secret, token)
            QMessageBox.information(
                self, "2FA Enabled", "Two-Factor Authentication is now enabled for your account!"
            )
            self.accept()
        except Exception as e:
            self.lbl_error.setText(f"Verification Failed: {e}")
            self.lbl_error.setVisible(True)
            self.input_token.selectAll()
            self.input_token.setFocus()

    def _on_disable_clicked(self) -> None:
        if not self.auth_service or not self.user_session:
            return

        reply = QMessageBox.question(
            self,
            "Disable 2FA",
            "Are you sure you want to disable Two-Factor Authentication?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.auth_service.disable_totp(self.user_session.user_id)
                QMessageBox.information(
                    self, "2FA Disabled", "Two-Factor Authentication has been disabled."
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
