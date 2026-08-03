"""
System Settings, CA Firm Profile & Ollama Model Manager Widget for FinAuditPro.
Provides Firm Branding (FRN, Membership No, Address), Live Ollama Engine Diagnostic,
and Air-Gapped Local Database Backup Manager.
"""

import os
import shutil
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QLineEdit, QComboBox, 
                               QFormLayout, QMessageBox, QCheckBox, QTabWidget, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import requests
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from core.config import config, get_default_data_dir
from database.database import DB_PATH

class SettingsWidget(QWidget):
    """CA Firm Settings & AI Ollama Model Configuration Manager Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f5f5f7;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Action Bar Header
        header = QFrame()
        header.setFixedHeight(68)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e5e5ea;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("System Settings & CA Firm Configuration")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f; letter-spacing: -0.4px; border: none;")
        subtitle = QLabel("CA Firm Registration, Ollama Model Diagnostics & Database Encryption")
        subtitle.setStyleSheet("font-size: 12px; color: #6e6e73; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()
        
        btn_save = QPushButton("Save Configuration")
        btn_save.setToolTip("Save system settings and CA firm configuration")
        btn_save.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #0062cc; }
        """)
        btn_save.clicked.connect(self.save_settings)
        h_layout.addWidget(btn_save)
        
        main_layout.addWidget(header)

        # 2. Main Tabbed Container
        tabs = QTabWidget()
        tabs.setToolTip("System settings and configuration tabs")
        tabs.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e5e5ea; background: #ffffff; border-radius: 8px; margin: 16px; }
            QTabBar::tab { background: #f5f5f7; color: #6e6e73; padding: 10px 20px; font-weight: 600; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
            QTabBar::tab:selected { background: #ffffff; color: #007aff; border: 1px solid #e5e5ea; border-bottom: none; }
        """)

        tabs.addTab(self._create_firm_profile_tab(), "CA Firm Profile & Branding")
        tabs.addTab(self._create_ai_engine_tab(), "Ollama AI Model & RAG Engine")
        tabs.addTab(self._create_security_db_tab(), "Air-Gap Security & Database Backup")

        main_layout.addWidget(tabs)

    def _create_firm_profile_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet("background-color: #ffffff; border: 1px solid #e5e5ea; border-radius: 12px; padding: 16px;")
        f_layout = QFormLayout(card)
        f_layout.setSpacing(12)

        self.firm_name = QLineEdit(config.ca_firm_name)
        self.frn_number = QLineEdit(config.ca_frn)
        self.member_no = QLineEdit(config.ca_membership_no)
        self.partner_name = QLineEdit(config.ca_name)
        self.firm_address = QLineEdit(getattr(config, 'ca_address', 'Suite 401, Corporate Heights, BKC, Mumbai - 400051'))

        for input_field in [self.firm_name, self.frn_number, self.member_no, self.partner_name, self.firm_address]:
            input_field.setStyleSheet("padding: 8px; border: 1px solid #e5e5ea; border-radius: 8px; background-color: #ffffff; font-size: 13px; color: #1d1d1f;")

        f_layout.addRow(QLabel("<b style='color:#1d1d1f;'>CA Firm Name *</b>"), self.firm_name)
        f_layout.addRow(QLabel("<b style='color:#1d1d1f;'>Firm Registration Number (FRN) *</b>"), self.frn_number)
        f_layout.addRow(QLabel("<b style='color:#1d1d1f;'>Partner Membership Number *</b>"), self.member_no)
        f_layout.addRow(QLabel("<b style='color:#1d1d1f;'>Managing Partner Name</b>"), self.partner_name)
        f_layout.addRow(QLabel("<b style='color:#1d1d1f;'>Registered Office Address</b>"), self.firm_address)

        w_layout.addWidget(card)
        w_layout.addStretch()
        return widget

    def _create_ai_engine_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px;")
        f_layout = QFormLayout(card)
        f_layout.setSpacing(12)

        self.ollama_url = QLineEdit(config.ollama_host)
        self.ollama_url.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;")
        f_layout.addRow("Ollama Local Endpoint URL:", self.ollama_url)

        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.model_combo.addItems(["llama3.2:latest", "mistral:latest", "qwen2.5:latest", "deepseek-r1:latest"])

        f_layout.addRow("Local Model Target:", self.model_combo)

        btn_test_ollama = QPushButton(" Test Ollama Connection")
        btn_test_ollama.setStyleSheet("padding: 6px 12px; background-color: #f1f5f9; color: #0284c7; border: 1px solid #bae6fd; font-weight: bold; border-radius: 6px;")
        btn_test_ollama.clicked.connect(self.test_ollama)
        f_layout.addRow("Diagnostics:", btn_test_ollama)

        w_layout.addWidget(card)
        w_layout.addStretch()
        return widget

    def _create_security_db_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px;")
        f_layout = QFormLayout(card)
        f_layout.setSpacing(12)

        sec_badge = QLabel(" AIR-GAPPED ENVIRONMENT: 100% Offline Local Storage Mode Active")
        sec_badge.setStyleSheet("background-color: #ecfdf5; color: #047857; font-weight: bold; padding: 8px; border-radius: 6px; font-size: 12px;")
        f_layout.addRow(sec_badge)

        self.db_path = QLineEdit(DB_PATH)
        self.db_path.setReadOnly(True)
        self.db_path.setStyleSheet("padding: 8px; border: 1px solid #e2e8f0; background-color: #f8fafc; border-radius: 6px;")
        f_layout.addRow("SQLite Database Location:", self.db_path)

        btn_backup = QPushButton(" Export Database Backup Zip")
        btn_backup.setStyleSheet("padding: 8px 14px; background-color: #0ea5e9; color: white; border-radius: 6px; font-weight: bold; border: none;")
        btn_backup.clicked.connect(self.backup_database)
        
        btn_restore = QPushButton(" Restore Database Backup")
        btn_restore.setStyleSheet("padding: 8px 14px; background-color: #0284c7; color: white; border-radius: 6px; font-weight: bold; border: none;")
        btn_restore.clicked.connect(self.restore_database_backup)

        btn_box = QHBoxLayout()
        btn_box.addWidget(btn_backup)
        btn_box.addWidget(btn_restore)
        f_layout.addRow("Disaster Recovery:", btn_box)

        btn_enable_master_pass = QPushButton(" Enable Master Password Encryption")
        btn_enable_master_pass.setStyleSheet("padding: 8px 14px; background-color: #0f766e; color: white; border-radius: 6px; font-weight: bold; border: none;")
        btn_enable_master_pass.clicked.connect(self.enable_master_password)
        f_layout.addRow("AES Master Encryption:", btn_enable_master_pass)

        w_layout.addWidget(card)
        w_layout.addStretch()
        return widget

    def test_ollama(self):
        try:
            url = self.ollama_url.text().strip()
            res = requests.get(f"{url}/api/tags", timeout=3)
            if res.status_code == 200:
                QMessageBox.information(self, "Ollama Active", f"Successfully connected to local Ollama daemon at {url}!")
            else:
                QMessageBox.warning(self, "Connection Error", f"Ollama returned HTTP status {res.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Ollama Offline", f"Could not reach Ollama at {self.ollama_url.text()}: {e}")

    def enable_master_password(self):
        from PySide6.QtWidgets import QInputDialog
        from security.security_manager import SecurityManager

        reply = QMessageBox.warning(
            self,
            "Security Warning — Master Password Encryption",
            "Enabling Master Password Encryption will protect all stored client statutory data with AES-256-GCM envelope encryption.\n\n"
            "CRITICAL: If you lose or forget this master password, encrypted client data CANNOT be recovered by any means.\n\n"
            "Do you wish to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        pass_key, ok = QInputDialog.getText(self, "Set Master Encryption Key", "Enter Master Password:", QLineEdit.EchoMode.Password)
        if ok and pass_key.strip():
            try:
                sm = SecurityManager()
                sm.enable_master_password_encryption(pass_key.strip())
                QMessageBox.information(self, "Encryption Activated", "Master password envelope encryption has been successfully enabled for this installation.")
            except Exception as e:
                QMessageBox.critical(self, "Encryption Failure", f"Failed to enable master password encryption: {e}")
        elif ok:
            QMessageBox.warning(self, "Invalid Password", "Master password cannot be blank.")

    def save_settings(self):
        try:
            import json
            config.ca_firm_name = self.firm_name.text().strip() or "Default CA Firm"
            config.ca_frn = self.frn_number.text().strip() or "000000W"
            config.ca_membership_no = self.member_no.text().strip() or "000000"
            config.ca_name = self.partner_name.text().strip() or "Default CA Name"
            
            os.environ["FINAUDIT_CA_FIRM_NAME"] = config.ca_firm_name
            os.environ["FINAUDIT_CA_FRN"] = config.ca_frn
            os.environ["FINAUDIT_CA_MEMBERSHIP_NO"] = config.ca_membership_no
            os.environ["FINAUDIT_CA_NAME"] = config.ca_name

            # Persist settings to JSON
            settings_path = os.path.join(get_default_data_dir(), "settings.json")
            user_settings = {
                "ca_firm_name": config.ca_firm_name,
                "ca_frn": config.ca_frn,
                "ca_membership_no": config.ca_membership_no,
                "ca_name": config.ca_name
            }
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(user_settings, f, indent=4)

            QMessageBox.information(self, "Settings Saved", "CA Firm Profile and System Settings saved successfully!")
        except Exception as e:
            self.error_widget = ErrorStateWidget("Save Settings Error", str(e))

    def backup_database(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Database Backup", "finauditpro_backup.db", "Database Files (*.db)")
        if not file_path: return
        try:
            src = DB_PATH
            if os.path.exists(src):
                shutil.copy(src, file_path)
                QMessageBox.information(self, "Backup Successful", f"Database backup exported to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Backup Warning", f"Main database file {DB_PATH} not found.")
        except Exception as e:
            self.error_widget = ErrorStateWidget("Database Backup Error", str(e))
            QMessageBox.critical(self, "Backup Error", f"Failed to export backup: {e}")

    def restore_database_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Backup Archive to Restore", "", "Backup Files (*.enc *.zip *.db)")
        if not file_path:
            return

        reply = QMessageBox.warning(
            self,
            "Confirm Database Restoration",
            "Restoring a database backup will overwrite existing database records with the contents of the backup archive.\n\nAre you sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from security.backup import BackupEngine
            be = BackupEngine()
            success = be.restore_backup(file_path)
            if success:
                QMessageBox.information(
                    self,
                    "Restoration Complete",
                    f"Database backup successfully restored from:\n{file_path}\n\nPlease restart FinAuditPro to apply all restored database changes."
                )
            else:
                QMessageBox.warning(self, "Restoration Warning", "Backup restoration could not complete successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Restoration Error", f"Failed to restore backup: {e}")

    def closeEvent(self, event):
        event.accept()
