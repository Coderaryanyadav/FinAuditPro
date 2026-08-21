"""
System Settings, CA Firm Profile & Ollama Model Manager Workspace for FinAuditPro.
Provides a 2-Pane Settings Layout (Left Category Navigation & Right Content Workspace),
Air-Gapped Security Manager, Ollama AI Diagnostics, and Database Backup Vault.
"""

import os
import json
import shutil
import logging
import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QLineEdit, QComboBox, 
                               QStackedWidget, QFileDialog, QDialog, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from core.config import config, get_default_data_dir
from database.database import DB_PATH

logger = logging.getLogger(__name__)

class InAppNotificationDialog(QDialog):
    """Custom in-app notification modal."""
    def __init__(self, title: str, message: str, is_warning: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(400)
        self.setStyleSheet("background-color: #FFFFFF; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel(title)
        fg_color = "#DC2626" if is_warning else "#2563EB"
        header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {fg_color}; border: none;")
        layout.addWidget(header)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 12px; color: #374151; line-height: 1.5; border: none;")
        layout.addWidget(msg)

        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setObjectName("primaryBtn")
        btn_ok.clicked.connect(self.accept)

        btn_r = QHBoxLayout()
        btn_r.addStretch()
        btn_r.addWidget(btn_ok)
        layout.addLayout(btn_r)

class SettingsWidget(QFrame):
    """CA Firm Settings & AI Ollama Model Configuration Workspace Widget."""

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("appBg")
        self._active_engagement_id = None
        self._active_project_id = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Action Bar Header
        header = QFrame()
        header.setFixedHeight(52)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setObjectName("contentHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("System Settings & CA Firm Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827; letter-spacing: -0.2px; border: none;")
        subtitle = QLabel("CA Firm profile, local AI engine, and database configuration.")
        subtitle.setStyleSheet("font-size: 11px; color: #6B7280; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        btn_save = QPushButton("Save Configuration")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.save_settings)
        h_layout.addWidget(btn_save)

        main_layout.addWidget(header)

        # 2. Main 2-Pane Settings Workspace Layout
        workspace = QFrame()
        workspace.setStyleSheet("background-color: #F7F8FA;")
        w_layout = QHBoxLayout(workspace)
        w_layout.setContentsMargins(24, 20, 24, 24)
        w_layout.setSpacing(20)

        # Left Settings Navigation (190px)
        nav_card = QFrame()
        nav_card.setFixedWidth(190)
        nav_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        n_layout = QVBoxLayout(nav_card)
        n_layout.setContentsMargins(8, 10, 8, 10)
        n_layout.setSpacing(2)

        nav_title = QLabel("SETTINGS")
        nav_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #9CA3AF; padding: 4px 8px 8px 8px; letter-spacing: 0.5px; border: none;")
        n_layout.addWidget(nav_title)

        self.nav_btns = []
        categories = [
            ("⊙  General Profile", 0),
            ("⚙  Local AI Engine",  1),
            ("⚿  Security & Database", 2)
        ]

        for text, idx in categories:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 10px;
                    font-size: 12px;
                    font-weight: 500;
                    color: #6B7280;
                    background: transparent;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover { background-color: #F7F8FA; color: #111827; }
                QPushButton:checked {
                    background-color: #EFF6FF;
                    color: #2563EB;
                    font-weight: 600;
                    border-left: 2px solid #2563EB;
                    border-radius: 0px;
                    border-top-right-radius: 5px;
                    border-bottom-right-radius: 5px;
                    padding-left: 8px;
                }
            """)
            btn.clicked.connect(lambda checked=False, i=idx: self._switch_tab(i))
            n_layout.addWidget(btn)
            self.nav_btns.append(btn)

        n_layout.addStretch()
        w_layout.addWidget(nav_card)

        # Right Content: scroll area with max-width constrained form
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        right_scroll.setStyleSheet("background: transparent; border: none;")

        right_container = QWidget()
        right_container.setStyleSheet("background: transparent;")
        rc_layout = QHBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        self.stack.setMaximumWidth(660)

        self.stack.addWidget(self._create_firm_profile_page())
        self.stack.addWidget(self._create_ai_engine_page())
        self.stack.addWidget(self._create_security_db_page())

        rc_layout.addWidget(self.stack)
        rc_layout.addStretch()
        right_scroll.setWidget(right_container)

        w_layout.addWidget(right_scroll, 1)
        main_layout.addWidget(workspace, 1)

    @property
    def active_engagement_id(self):
        return self._active_engagement_id

    @active_engagement_id.setter
    def active_engagement_id(self, val):
        self._active_engagement_id = val

    @property
    def active_project_id(self):
        return self._active_project_id

    @active_project_id.setter
    def active_project_id(self, val):
        self._active_project_id = val

    def refresh_data(self):
        pass

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == index)

    def _show_app_notification(self, title: str, message: str, is_warning: bool = False):
        dlg = InAppNotificationDialog(title, message, is_warning, self)
        dlg.exec()

    def _create_firm_profile_page(self) -> QWidget:
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 18, 20, 18)
        cl.setSpacing(16)

        t = QLabel("CA Firm Profile & Regulatory Identity")
        t.setStyleSheet("font-size: 14px; font-weight: 600; color: #111827; border-bottom: 1px solid #E5E7EB; padding-bottom: 10px; border: none;")
        cl.addWidget(t)

        def add_form_row(label_text, input_widget, helper_text=""):
            row = QVBoxLayout()
            row.setSpacing(5)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.3px; border: none;")
            row.addWidget(lbl)
            row.addWidget(input_widget)
            if helper_text:
                hlp = QLabel(helper_text)
                hlp.setStyleSheet("font-size: 11px; color: #9CA3AF; border: none;")
                row.addWidget(hlp)
            cl.addLayout(row)

        self.firm_name = QLineEdit(config.ca_firm_name)
        add_form_row("Firm Legal Name *", self.firm_name, "Legal registered name of Chartered Accountancy firm")

        self.frn_number = QLineEdit(config.ca_frn)
        add_form_row("Firm Registration Number (FRN) *", self.frn_number, "7-character ICAI Firm Registration Number")

        self.member_no = QLineEdit(config.ca_membership_no)
        add_form_row("CA Membership Number *", self.member_no, "6-digit ICAI CA Membership Number")

        self.partner_name = QLineEdit(config.ca_name)
        add_form_row("Signing Partner Name *", self.partner_name, "Name of primary audit signing partner")

        self.firm_address = QLineEdit(config.ca_address)
        self.firm_address.setStyleSheet("padding: 7px 10px; border: 1px solid #e1e8f4; border-radius: 6px; font-size: 12px; color: #0f172a;")
        add_form_row("Firm Office Address", self.firm_address, "Registered office address for report headers")

        l.addWidget(card)
        l.addStretch()
        return widget

    def _create_ai_engine_page(self) -> QWidget:
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12)

        # Status Banner Card
        self.status_card = QFrame()
        self.status_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        s_layout = QHBoxLayout(self.status_card)
        s_layout.setContentsMargins(16, 12, 16, 12)

        st_v = QVBoxLayout()
        st_v.setSpacing(4)
        self.lbl_ollama_status = QLabel("● CONNECTED TO OLLAMA AI ENGINE")
        self.lbl_ollama_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #059669; border: none;")
        lbl_sub = QLabel("Local RAG Engine active and responding at localhost:11434")
        lbl_sub.setStyleSheet("font-size: 11px; color: #6B7280; border: none;")
        st_v.addWidget(self.lbl_ollama_status)
        st_v.addWidget(lbl_sub)
        s_layout.addLayout(st_v)

        s_layout.addStretch()

        btn_test = QPushButton("Test Connection")
        btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_test.setObjectName("secondaryBtn")
        btn_test.clicked.connect(self.test_ollama)
        s_layout.addWidget(btn_test)
        l.addWidget(self.status_card)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 18, 20, 18)
        cl.setSpacing(14)

        t = QLabel("Local AI Engine & Ollama Configuration")
        t.setStyleSheet("font-size: 14px; font-weight: 600; color: #111827; padding-bottom: 10px; border: none;")
        cl.addWidget(t)

        self.ollama_url = QLineEdit(config.ollama_host)
        lbl_u = QLabel("OLLAMA ENDPOINT URL")
        lbl_u.setStyleSheet("font-size: 11px; font-weight: 600; color: #6B7280; letter-spacing: 0.3px; border: none;")
        cl.addWidget(lbl_u)
        cl.addWidget(self.ollama_url)

        self.model_combo = QComboBox()
        try:
            res = requests.get(f"{config.ollama_host}/api/tags", timeout=2)
            if res.status_code == 200:
                installed_models = [m.get("name", "") for m in res.json().get("models", [])]
                if installed_models:
                    self.model_combo.addItems(installed_models)
                else:
                    self.model_combo.addItems(["qwen3.5:9b-mlx", "llama3.2:latest", "deepseek-r1:latest"])
            else:
                self.model_combo.addItems(["qwen3.5:9b-mlx", "llama3.2:latest", "deepseek-r1:latest"])
        except Exception:
            self.model_combo.addItems(["qwen3.5:9b-mlx", "llama3.2:latest", "deepseek-r1:latest"])

        lbl_m = QLabel("LOCAL MODEL")
        lbl_m.setStyleSheet("font-size: 11px; font-weight: 600; color: #6B7280; letter-spacing: 0.3px; border: none;")
        cl.addWidget(lbl_m)
        cl.addWidget(self.model_combo)

        l.addWidget(card)
        l.addStretch()
        return widget

    def _create_security_db_page(self) -> QWidget:
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(12)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 18, 20, 18)
        cl.setSpacing(14)

        t = QLabel("Air-Gap Security & Database Vault Manager")
        t.setStyleSheet("font-size: 14px; font-weight: 600; color: #111827; padding-bottom: 10px; border: none;")
        cl.addWidget(t)

        sec_badge = QLabel("✓  Air-Gapped — 100% Offline Local SQLite Mode Active")
        sec_badge.setStyleSheet("background-color: #ECFDF5; color: #059669; font-weight: 600; padding: 7px 12px; border-radius: 6px; font-size: 11px; border: 1px solid #A7F3D0;")
        cl.addWidget(sec_badge)

        lbl_db = QLabel("DATABASE STORAGE PATH")
        lbl_db.setStyleSheet("font-size: 11px; font-weight: 600; color: #6B7280; letter-spacing: 0.3px; border: none;")
        self.db_path = QLineEdit(DB_PATH)
        self.db_path.setReadOnly(True)
        cl.addWidget(lbl_db)
        cl.addWidget(self.db_path)

        btn_r = QHBoxLayout()
        btn_r.setSpacing(10)

        btn_backup = QPushButton("Export Database Backup")
        btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_backup.setObjectName("primaryBtn")
        btn_backup.clicked.connect(self.backup_database)

        btn_restore = QPushButton("Restore Database Backup")
        btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restore.setObjectName("secondaryBtn")
        btn_restore.clicked.connect(self.restore_database_backup)

        btn_r.addWidget(btn_backup)
        btn_r.addWidget(btn_restore)
        cl.addLayout(btn_r)

        l.addWidget(card)
        l.addStretch()
        return widget

    def test_ollama(self):
        try:
            url = self.ollama_url.text().strip()
            res = requests.get(f"{url}/api/tags", timeout=3)
            if res.status_code == 200:
                self.lbl_ollama_status.setText("● CONNECTED TO OLLAMA AI ENGINE")
                self.lbl_ollama_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #059669; border: none;")
                self._show_app_notification("Connected", f"Ollama online at {url}.")
            else:
                self.lbl_ollama_status.setText("● OLLAMA RESPONSE WARNING")
                self.lbl_ollama_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #D97706; border: none;")
                self._show_app_notification("Warning", f"Ollama returned HTTP {res.status_code}.", is_warning=True)
        except Exception as e:
            self.lbl_ollama_status.setText("● OLLAMA OFFLINE")
            self.lbl_ollama_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #DC2626; border: none;")
            self._show_app_notification("Offline", f"Could not reach Ollama: {e}", is_warning=True)

    def save_settings(self):
        try:
            config.ca_firm_name = self.firm_name.text().strip() or "Default CA Firm"
            config.ca_frn = self.frn_number.text().strip() or "000000W"
            config.ca_membership_no = self.member_no.text().strip() or "000000"
            config.ca_name = self.partner_name.text().strip() or "Default CA Name"
            config.ca_address = self.firm_address.text().strip() or "Suite 401, Corporate Heights, BKC, Mumbai - 400051"
            
            os.environ["FINAUDIT_CA_FIRM_NAME"] = config.ca_firm_name
            os.environ["FINAUDIT_CA_FRN"] = config.ca_frn
            os.environ["FINAUDIT_CA_MEMBERSHIP_NO"] = config.ca_membership_no
            os.environ["FINAUDIT_CA_NAME"] = config.ca_name
            os.environ["FINAUDIT_CA_ADDRESS"] = config.ca_address

            settings_path = os.path.join(get_default_data_dir(), "settings.json")
            user_settings = {
                "ca_firm_name": config.ca_firm_name,
                "ca_frn": config.ca_frn,
                "ca_membership_no": config.ca_membership_no,
                "ca_name": config.ca_name,
                "ca_address": config.ca_address
            }
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(user_settings, f, indent=4)

            self._show_app_notification("Settings Saved", "CA Firm Profile and System Configuration saved successfully!")
        except Exception as e:
            self._show_app_notification("Save Error", f"Could not save settings: {e}", is_warning=True)

    def backup_database(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Database Backup", "finauditpro_backup.db", "Database Files (*.db)")
        if not file_path: return
        try:
            src = DB_PATH
            if os.path.exists(src):
                shutil.copy(src, file_path)
                self._show_app_notification("Backup Successful", f"Database backup exported to:\n\n{file_path}")
            else:
                self._show_app_notification("Backup Error", f"Main database file {DB_PATH} not found.", is_warning=True)
        except Exception as e:
            self._show_app_notification("Backup Error", f"Failed to export backup: {e}", is_warning=True)

    def restore_database_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Database Backup File", "", "Database Files (*.db)")
        if not file_path: return
        try:
            if os.path.exists(file_path):
                shutil.copy(file_path, DB_PATH)
                self._show_app_notification("Restore Successful", "Database restored successfully. Please restart FinAuditPro.")
            else:
                self._show_app_notification("Restore Error", "Selected backup file does not exist.", is_warning=True)
        except Exception as e:
            self._show_app_notification("Restore Failure", f"Failed to restore database: {e}", is_warning=True)

    def closeEvent(self, event):
        event.accept()
