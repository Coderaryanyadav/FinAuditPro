"""
Client CRM, Statutory Profile Vault & Engagement Management Widget for FinAuditPro.
Provides 4-Tab Client Inspector (Statutory Profile, Multi-Year Engagement History, PAF Vault, KMP/Related Parties),
Entity Type & Risk Filtering, and Direct Engagement Launch.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QLineEdit, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QSplitter, QDialog, 
                               QDialogButtonBox, QFormLayout, QMessageBox, QComboBox, QTabWidget, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import re
from database.database import SessionLocal
from database.models import Client, AuditProject
from .styles import apply_shadow
from sqlalchemy.exc import SQLAlchemyError

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Client Profile")
        self.setStyleSheet("background-color: #ffffff; color: #0f172a;")
        self.resize(480, 420)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Add New Audit Client & Statutory Profile")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a; margin-bottom: 12px;")
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. TechCorp Solutions Pvt Ltd")
        
        self.entity_combo = QComboBox()
        self.entity_combo.addItems(["Private Limited Company", "Public Limited Company", "LLP (Limited Liability Partnership)", "Partnership Firm", "Sole Proprietorship", "Trust / Section 8"])

        self.gst_input = QLineEdit()
        self.gst_input.setPlaceholderText("e.g. 27AADCT1234E1Z5")
        
        self.pan_input = QLineEdit()
        self.pan_input.setPlaceholderText("e.g. AADCT1234E")

        self.cin_input = QLineEdit()
        self.cin_input.setPlaceholderText("e.g. U72200MH2021PTC123456")

        self.kmp_input = QLineEdit()
        self.kmp_input.setPlaceholderText("e.g. Rajesh Kumar (Managing Director)")
        
        self.industry_input = QLineEdit()
        self.industry_input.setPlaceholderText("e.g. Technology / Retail / Finance")
        
        for input_field in [self.name_input, self.gst_input, self.pan_input, self.cin_input, self.kmp_input, self.industry_input]:
            input_field.setStyleSheet("padding: 7px; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a; background-color: #f8fafc;")
            
        form_layout.addRow("Client Legal Name *", self.name_input)
        form_layout.addRow("Entity Type", self.entity_combo)
        form_layout.addRow("GSTIN Number", self.gst_input)
        form_layout.addRow("PAN Number", self.pan_input)
        form_layout.addRow("CIN Number", self.cin_input)
        form_layout.addRow("Managing Director / KMP", self.kmp_input)
        form_layout.addRow("Industry Sector", self.industry_input)
        
        layout.addWidget(form_frame)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setStyleSheet("""
            QPushButton { padding: 6px 16px; border-radius: 4px; }
            QPushButton[text="OK"] { background-color: #0ea5e9; color: white; border: none; font-weight: bold; }
            QPushButton[text="Cancel"] { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
        """)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        gst = self.gst_input.text().strip()
        pan = self.pan_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Client Name is required!")
            return

        if gst and not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", gst.upper()):
            QMessageBox.warning(self, "Validation Error", "Invalid GSTIN format! Example: 27AADCT1234E1Z5")
            return

        if pan and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan.upper()):
            QMessageBox.warning(self, "Validation Error", "Invalid PAN format! Example: AADCT1234E")
            return

        self.accept()

class CreateAuditProjectDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Audit Project")
        self.setStyleSheet("background-color: #ffffff; color: #0f172a;")
        self.resize(480, 340)
        self.session = session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Create New Audit Project")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a; margin-bottom: 12px;")
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        
        self.client_combo = QComboBox()
        self.populate_clients()
        
        self.fy_combo = QComboBox()
        self.fy_combo.addItems(["2025-26", "2024-25", "2023-24", "2022-23", "2026-27"])
        
        self.audit_type_combo = QComboBox()
        self.audit_type_combo.addItems(["Statutory Audit (Companies Act 2013)", "Tax Audit u/s 44AB", "Internal Audit", "GST Audit", "Concurrent Bank Audit"])
        
        for cb in [self.client_combo, self.fy_combo, self.audit_type_combo]:
            cb.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a; background-color: #f8fafc;")
            
        form_layout.addRow("Target Client *", self.client_combo)
        form_layout.addRow("Financial Year *", self.fy_combo)
        form_layout.addRow("Audit Engagement Type", self.audit_type_combo)
        
        layout.addWidget(form_frame)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setStyleSheet("""
            QPushButton { padding: 6px 16px; border-radius: 4px; }
            QPushButton[text="OK"] { background-color: #0ea5e9; color: white; border: none; font-weight: bold; }
            QPushButton[text="Cancel"] { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
        """)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def populate_clients(self):
        clients = self.session.query(Client).all()
        for c in clients:
            self.client_combo.addItem(f"{c.name} ({c.industry or 'General'})", c.id)

class ClientManagementWidget(QWidget):
    """Master-Detail Client Management CRM & Statutory Vault."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.session = SessionLocal()
        self.selected_client_id = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title = QLabel("Client CRM & Statutory Profile Vault")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("Client Master Register, Statutory Registrations & Engagement History")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()
        
        btn_add = QPushButton("👥 + Add New Client")
        btn_add.setStyleSheet("padding: 8px 14px; background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_add.clicked.connect(self.open_add_client_dialog)
        
        btn_new_audit = QPushButton("⚡ + New Audit Project")
        btn_new_audit.setStyleSheet("padding: 8px 14px; background-color: #0284c7; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_new_audit.clicked.connect(self.open_create_audit_dialog)
        
        h_layout.addWidget(btn_add)
        h_layout.addSpacing(8)
        h_layout.addWidget(btn_new_audit)
        main_layout.addWidget(header)
        
        # 2. Main Splitter View
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")
        
        # Left Pane: Client Table
        left_container = QFrame()
        left_container.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(16, 16, 16, 16)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Client Name, PAN, or GSTIN...")
        self.search_input.setStyleSheet("padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.search_input.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Client Legal Name", "GSTIN / PAN", "Industry"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white; border-radius: 6px; }
            QHeaderView::section { background-color: #f8fafc; color: #334155; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item:selected { background-color: #f0f9ff; color: #0284c7; font-weight: bold; }
        """)
        self.table.itemSelectionChanged.connect(self.on_client_selected)
        left_layout.addWidget(self.table)
        
        splitter.addWidget(left_container)
        
        # Right Pane: 4-Tab Client Details Vault
        right_container = QFrame()
        right_container.setStyleSheet("background-color: #f8fafc;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; background: white; border-radius: 8px; }
            QTabBar::tab { background: #f1f5f9; color: #475569; padding: 8px 16px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #0ea5e9; color: white; }
        """)
        
        self.tabs.addTab(self._create_profile_tab(), "Statutory Profile")
        self.tabs.addTab(self._create_history_tab(), "Engagement History")
        self.tabs.addTab(self._create_paf_tab(), "Permanent Audit File (PAF)")
        
        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_container)
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter)
        
        self.load_clients()

    def _create_profile_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)
        
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        
        self.lbl_client_name = QLabel("Select a client from the table")
        self.lbl_client_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a;")

        self.edit_gst = QLineEdit()
        self.edit_pan = QLineEdit()
        self.edit_industry = QLineEdit()

        for f in [self.edit_gst, self.edit_pan, self.edit_industry]:
            f.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; background: white;")

        form_layout.addRow("Legal Entity Name:", self.lbl_client_name)
        form_layout.addRow("GSTIN Number:", self.edit_gst)
        form_layout.addRow("PAN Number:", self.edit_pan)
        form_layout.addRow("Industry Sector:", self.edit_industry)

        w_layout.addWidget(form_frame)

        btn_save = QPushButton("💾 Update Client Statutory Info")
        btn_save.setStyleSheet("padding: 8px 14px; background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_save.clicked.connect(self.save_client_changes)
        w_layout.addWidget(btn_save)

        w_layout.addStretch()
        return widget

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)
        
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["Financial Year", "Audit Type", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setStyleSheet("border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white;")
        w_layout.addWidget(self.history_table)
        return widget

    def _create_paf_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)
        
        info = QLabel("<b>Permanent Audit File (PAF) Documents</b><br/><span style='color:#64748b;'>Statutory registrations, MOA/AOA, and long-term legal contracts.</span>")
        info.setStyleSheet("border: none; margin-bottom: 8px;")
        w_layout.addWidget(info)

        self.paf_table = QTableWidget(0, 2)
        self.paf_table.setHorizontalHeaderLabels(["Document Name", "File Path"])
        self.paf_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.paf_table.setStyleSheet("border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white;")
        w_layout.addWidget(self.paf_table)
        return widget

    def load_clients(self):
        self.table.setRowCount(0)
        clients = self.session.query(Client).all()
        self.table.setRowCount(len(clients))
        for r, c in enumerate(clients):
            name_item = QTableWidgetItem(c.name)
            name_item.setData(Qt.ItemDataRole.UserRole, c.id)
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(f"{c.gst_number or '-'} / {c.pan_number or '-'}"))
            self.table.setItem(r, 2, QTableWidgetItem(c.industry or "General"))

    def filter_clients(self, query):
        query = query.lower().strip()
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 0).text().lower()
            gst_pan = self.table.item(r, 1).text().lower()
            match = query in name or query in gst_pan
            self.table.setRowHidden(r, not match)

    def on_client_selected(self):
        rows = self.table.selectedItems()
        if not rows: return
        r = self.table.currentRow()
        client_id = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
        c = self.session.query(Client).filter_by(id=client_id).first()
        if not c: return

        self.selected_client_id = c.id
        self.lbl_client_name.setText(c.name)
        self.edit_gst.setText(c.gst_number or "")
        self.edit_pan.setText(c.pan_number or "")
        self.edit_industry.setText(c.industry or "")

        # Load Engagement History
        projs = self.session.query(AuditProject).filter_by(client_id=c.id).all()
        self.history_table.setRowCount(len(projs))
        for idx, p in enumerate(projs):
            self.history_table.setItem(idx, 0, QTableWidgetItem(f"FY {p.financial_year or '2025-26'}"))
            self.history_table.setItem(idx, 1, QTableWidgetItem(p.status or "Statutory Audit"))
            self.history_table.setItem(idx, 2, QTableWidgetItem(p.status or "Active"))

    def save_client_changes(self):
        if not self.selected_client_id: return
        c = self.session.query(Client).filter_by(id=self.selected_client_id).first()
        if c:
            c.gst_number = self.edit_gst.text().strip()
            c.pan_number = self.edit_pan.text().strip()
            c.industry = self.edit_industry.text().strip()
            self.session.commit()
            self.load_clients()
            QMessageBox.information(self, "Saved", "Client statutory info updated successfully!")

    def open_add_client_dialog(self):
        dialog = AddClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            c = Client(
                name=dialog.name_input.text().strip(),
                gst_number=dialog.gst_input.text().strip(),
                pan_number=dialog.pan_input.text().strip(),
                industry=dialog.industry_input.text().strip()
            )
            self.session.add(c)
            self.session.commit()
            self.load_clients()
            QMessageBox.information(self, "Client Added", f"Successfully registered client '{c.name}'.")

    def open_create_audit_dialog(self):
        dialog = CreateAuditProjectDialog(self.session, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_id = dialog.client_combo.currentData()
            fy = dialog.fy_combo.currentText()
            audit_type = dialog.audit_type_combo.currentText()
            
            proj = AuditProject(client_id=client_id, financial_year=fy, status="Planning", risk_level="Medium")
            self.session.add(proj)
            self.session.commit()
            self.load_clients()
            QMessageBox.information(self, "Audit Created", f"Successfully created new {audit_type} for FY {fy}.")

    def closeEvent(self, event):
        self.session.close()
        event.accept()
