"""System Settings & Environment Diagnostics Workspace View."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
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
from finauditpro.ui.theme import CardWidget
from finauditpro.version import get_build_info


class SettingsView(QWidget):
    """Workspace view managing LM Studio endpoints, cloud AI opt-outs, and diagnostics."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.settings_service = SettingsService()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h2>System Settings & Platform Configuration</h2>"))
        header_layout.addStretch()

        self.self_check_btn = QPushButton("📋 Run System Diagnostics")
        self.self_check_btn.setStyleSheet("background-color: #2b6cb0; color: white; font-weight: bold; padding: 6px 12px;")
        self.self_check_btn.clicked.connect(self._open_self_check)
        header_layout.addWidget(self.self_check_btn)

        layout.addLayout(header_layout)

        # Build Version Metadata Card
        build_info = get_build_info()
        info_card = CardWidget("Application Build & Environment Diagnostics")
        info_card.content_layout.addWidget(QLabel(f"<b>Application Name:</b> {build_info['app_name']} v{build_info['version']}"))
        info_card.content_layout.addWidget(QLabel(f"<b>Python Version:</b> {build_info['python_version']} | <b>Architecture:</b> {build_info['arch']}"))
        info_card.content_layout.addWidget(QLabel(f"<b>Platform:</b> {build_info['platform']} | <b>Offline Isolated:</b> {build_info['offline_isolated']}"))
        layout.addWidget(info_card)

        # Configuration Form Card
        config_card = CardWidget("Local AI & LLM Provider Configuration")
        form = QFormLayout()
        form.setSpacing(10)

        self.endpoint_input = QLineEdit()
        form.addRow("LM Studio Base URL:", self.endpoint_input)

        self.llm_input = QLineEdit()
        form.addRow("LLM Model Name:", self.llm_input)

        self.embed_input = QLineEdit()
        form.addRow("Embedding Model Name:", self.embed_input)

        self.cloud_optout_chk = QCheckBox("Enable External Cloud AI (Default: OFF / Disabled)")
        form.addRow("Cloud AI Opt-In Posture:", self.cloud_optout_chk)

        config_card.content_layout.addLayout(form)
        layout.addWidget(config_card)

        # Bottom Button Bar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("💾 Save Configuration Settings")
        save_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 9px 20px; font-size: 13px;")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()

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
        QMessageBox.information(self, "Settings Saved", "Application configuration settings saved successfully.")

    def _open_self_check(self) -> None:
        dlg = SelfCheckDialog(self)
        dlg.exec()
