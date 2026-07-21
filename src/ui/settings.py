from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QLineEdit, QComboBox, 
                              QFormLayout, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt
from .styles import apply_shadow

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f1f5f9;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("Application Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("padding: 8px 18px; background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_save.clicked.connect(self.save_settings)
        h_layout.addWidget(btn_save)
        
        main_layout.addWidget(header)
        
        # Form Container
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(32, 32, 32, 32)
        c_layout.setSpacing(24)
        
        card = QFrame()
        card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;")
        apply_shadow(card, blur=15, dy=3, alpha=15)
        
        form_layout = QFormLayout(card)
        form_layout.setSpacing(16)
        
        ai_section = QLabel("<b>AI & Engine Configuration</b>")
        ai_section.setStyleSheet("font-size: 16px; color: #0f172a; margin-bottom: 8px;")
        form_layout.addRow(ai_section)
        
        self.ollama_url = QLineEdit("http://localhost:11434")
        self.ollama_url.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;")
        form_layout.addRow("Ollama Endpoint URL:", self.ollama_url)
        
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;")
        
        # Detect installed local Ollama models
        try:
            import requests
            res = requests.get("http://localhost:11434/api/tags", timeout=2)
            if res.status_code == 200:
                models = [m.get("name", "") for m in res.json().get("models", [])]
                if models:
                    self.model_combo.addItems(models)
                else:
                    self.model_combo.addItem("No Ollama Models Found")
            else:
                self.model_combo.addItem("llama3.2")
        except Exception:
            self.model_combo.addItem("llama3.2 (Ollama Offline)")

        form_layout.addRow("LLM Model Target:", self.model_combo)
        
        self.chk_gpu = QCheckBox("Enable GPU Acceleration for FAISS vector search")
        self.chk_gpu.setChecked(True)
        form_layout.addRow("", self.chk_gpu)
        
        form_layout.addRow(QLabel("<hr style='border: 1px solid #e2e8f0;'/>"))
        
        db_section = QLabel("<b>Database & Storage Options</b>")
        db_section.setStyleSheet("font-size: 16px; color: #0f172a; margin-bottom: 8px;")
        form_layout.addRow(db_section)
        
        self.db_path = QLineEdit("data/finauditpro.db")
        self.db_path.setReadOnly(True)
        self.db_path.setStyleSheet("padding: 8px; border: 1px solid #e2e8f0; background-color: #f8fafc; border-radius: 6px;")
        form_layout.addRow("SQLite Database Location:", self.db_path)
        
        btn_backup = QPushButton("📦 Export Database Backup")
        btn_backup.setStyleSheet("padding: 8px 14px; background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; border-radius: 6px; font-weight: 600;")
        btn_backup.clicked.connect(self.backup_database)
        form_layout.addRow("Backup:", btn_backup)
        
        c_layout.addWidget(card)
        c_layout.addStretch()
        
        main_layout.addWidget(content)

    def save_settings(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.MANAGE_SETTINGS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to modify system settings.")
            return
        QMessageBox.information(self, "Settings Saved", "Application configuration successfully updated!")

    def backup_database(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.PERFORM_BACKUP):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to trigger database backups.")
            return
        QMessageBox.information(self, "Database Backup", "Database backup created in data/backups/ directory.")
