"""
System Settings & Environment Diagnostics Workspace View for FinAuditPro.
Manages LM Studio endpoints, cloud AI posture, user security, and platform diagnostics.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
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
from finauditpro.application.services.settings_service import AppSettings, SettingsService
from finauditpro.ui.dialogs.change_password_dialog import ChangePasswordDialog
from finauditpro.ui.dialogs.self_check_dialog import SelfCheckDialog
from finauditpro.ui.theme import CardWidget, PageHeader
from finauditpro.version import get_build_info


class SettingsView(QWidget):
    """Workspace view managing LM Studio endpoints, cloud AI opt-outs, and diagnostics."""

    def __init__(
        self,
        auth_service: AuthService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.settings_service = SettingsService()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Settings & System Diagnostics",
            subtitle="Local AI engine endpoints, security configuration, and runtime environment diagnostics.",
            action_text="Run Diagnostics",
            action_callback=self._open_self_check,
        )
        layout.addWidget(self.header)

        # 2. Build Version Metadata Card
        build_info = get_build_info()
        info_card = CardWidget("APPLICATION BUILD & RUNTIME DIAGNOSTICS")
        info_l = QVBoxLayout()
        info_l.setSpacing(6)

        info_l.addWidget(
            QLabel(f"<b>Application:</b> {build_info['app_name']} v{build_info['version']}")
        )
        info_l.addWidget(
            QLabel(
                f"<b>Python Version:</b> {build_info['python_version']} · <b>Architecture:</b> {build_info['arch']}"
            )
        )
        info_l.addWidget(
            QLabel(
                f"<b>Platform:</b> {build_info['platform']} · <b>Offline Isolated:</b> {build_info['offline_isolated']}"
            )
        )
        info_card.content_layout.addLayout(info_l)
        layout.addWidget(info_card)

        # 3. User Security & Password Management Card
        sec_card = CardWidget("SECURITY & AUDITOR ACCESS CREDENTIALS")
        sec_layout = QVBoxLayout()
        sec_layout.setSpacing(8)

        sec_desc = QLabel(
            "Manage your administrator master credentials or update account security settings."
        )
        sec_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        sec_layout.addWidget(sec_desc)

        sec_btn_row = QHBoxLayout()
        btn_change_pwd = QPushButton("Edit Profile && Credentials")
        btn_change_pwd.setObjectName("primaryButton")
        btn_change_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_change_pwd.clicked.connect(self._on_change_password_clicked)
        sec_btn_row.addWidget(btn_change_pwd)

        btn_2fa = QPushButton("Manage Two-Factor Auth (2FA)")
        btn_2fa.setObjectName("secondaryButton")
        btn_2fa.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_2fa.clicked.connect(self._on_manage_2fa_clicked)
        sec_btn_row.addWidget(btn_2fa)

        sec_btn_row.addStretch()
        sec_layout.addLayout(sec_btn_row)

        sec_card.content_layout.addLayout(sec_layout)
        layout.addWidget(sec_card)

        # 4. Local AI Configuration Form Card
        config_card = CardWidget("LOCAL AI & LLM PROVIDER CONFIGURATION")
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        field_style = """
            QLineEdit {
                border: 1px solid #CBD5E1; border-radius: 6px;
                padding: 7px 12px; font-size: 13px; color: #0F172A; background: #FFFFFF;
                min-width: 320px;
            }
            QLineEdit:focus { border-color: #2563EB; background: #FFFFFF; }
            QLineEdit::placeholder { color: #94A3B8; }
        """

        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("http://localhost:1234/v1")
        self.endpoint_input.setStyleSheet(field_style)
        form.addRow("LM Studio Base URL:", self.endpoint_input)

        self.llm_input = QLineEdit()
        self.llm_input.setPlaceholderText("e.g. qwen2.5-coder-7b-instruct")
        self.llm_input.setStyleSheet(field_style)
        form.addRow("LLM Model Name:", self.llm_input)

        self.embed_input = QLineEdit()
        self.embed_input.setPlaceholderText("e.g. text-embedding-nomic-embed-text-v1.5")
        self.embed_input.setStyleSheet(field_style)
        form.addRow("Embedding Model Name:", self.embed_input)

        self.cloud_optout_chk = QCheckBox(
            "Enable External Cloud AI (Default: OFF / Fully Isolated)"
        )
        form.addRow("Cloud AI Posture:", self.cloud_optout_chk)

        config_card.content_layout.addLayout(form)
        layout.addWidget(config_card)

        # 5. Save Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Save Configuration")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: #FFFFFF;
                font-size: 13px; font-weight: 600;
                border-radius: 6px; padding: 8px 22px; border: 1px solid transparent;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        layout.addStretch(1)

        self._load_settings()

    def _load_settings(self) -> None:
        settings = self.settings_service.get_settings()
        self.endpoint_input.setText(settings.lm_studio_endpoint)
        self.llm_input.setText(settings.llm_model)
        self.embed_input.setText(settings.embedding_model)
        self.cloud_optout_chk.setChecked(settings.allow_cloud_ai)

    def _save_settings(self) -> None:
        settings = AppSettings(
            lm_studio_endpoint=self.endpoint_input.text().strip(),
            llm_model=self.llm_input.text().strip(),
            embedding_model=self.embed_input.text().strip(),
            allow_cloud_ai=self.cloud_optout_chk.isChecked(),
        )
        self.settings_service.update_settings(settings)
        QMessageBox.information(
            self, "Settings Saved", "Application configuration settings saved successfully."
        )

    def _on_change_password_clicked(self) -> None:
        if not self.auth_service:
            QMessageBox.warning(self, "Security Error", "Authentication service is not available.")
            return

        users = self.auth_service.list_users()
        if not users:
            QMessageBox.warning(self, "Error", "No registered user found.")
            return

        primary_user = users[0]
        session = UserSession(
            user_id=primary_user.id,
            username=primary_user.username,
            role=primary_user.role,
            must_change_password=False,
        )

        dlg = ChangePasswordDialog(
            parent=self,
            auth_service=self.auth_service,
            user_session=session,
            is_forced=False,
        )
        dlg.exec()

    def _on_manage_2fa_clicked(self) -> None:
        win = self.window()
        if not hasattr(win, "current_user_session") or not win.current_user_session:
            return
        from finauditpro.ui.dialogs.totp_dialog import TOTPDialog
        dlg = TOTPDialog(self.window(), auth_service=self.auth_service, user_session=win.current_user_session)
        dlg.exec()

    def _open_self_check(self) -> None:
        SelfCheckDialog(self).exec()
