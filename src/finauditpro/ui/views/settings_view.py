"""
System Settings & Environment Diagnostics Workspace View for FinAuditPro.
Manages LM Studio endpoints, cloud AI posture, and platform diagnostics.
"""

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

from finauditpro.application.services.settings_service import AppSettings, SettingsService
from finauditpro.ui.dialogs.self_check_dialog import SelfCheckDialog
from finauditpro.ui.theme import CardWidget, PageHeader
from finauditpro.version import get_build_info


class SettingsView(QWidget):
    """Workspace view managing LM Studio endpoints, cloud AI opt-outs, and diagnostics."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.settings_service = SettingsService()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Settings & System Diagnostics",
            subtitle="Local AI engine endpoints, cloud opt-in security posture, and runtime environment diagnostics.",
            action_text="📋 Run Diagnostics",
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

        # 3. Local AI Configuration Form Card
        config_card = CardWidget("LOCAL AI & LLM PROVIDER CONFIGURATION")
        form = QFormLayout()
        form.setSpacing(10)

        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("http://localhost:1234/v1")
        form.addRow("LM Studio Base URL:", self.endpoint_input)

        self.llm_input = QLineEdit()
        self.llm_input.setPlaceholderText("e.g. qwen2.5-coder-7b-instruct")
        form.addRow("LLM Model Name:", self.llm_input)

        self.embed_input = QLineEdit()
        self.embed_input.setPlaceholderText("e.g. text-embedding-nomic-embed-text-v1.5")
        form.addRow("Embedding Model Name:", self.embed_input)

        self.cloud_optout_chk = QCheckBox(
            "Enable External Cloud AI (Default: OFF / Fully Isolated)"
        )
        form.addRow("Cloud AI Posture:", self.cloud_optout_chk)

        config_card.content_layout.addLayout(form)
        layout.addWidget(config_card)

        # 4. Save Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Save Configuration")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: #FFFFFF;
                font-size: 12px; font-weight: 600;
                border-radius: 6px; padding: 8px 20px; border: none;
            }
            QPushButton:hover { background-color: #1D4ED8; }
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

    def _open_self_check(self) -> None:
        SelfCheckDialog(self).exec()
