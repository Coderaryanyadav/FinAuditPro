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
from database.models import Client, AuditProject, KeyManagementPersonnel, ClientIndustry
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from sqlalchemy.exc import SQLAlchemyError

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Register New Client Entity")
        self.setStyleSheet("background-color: #ffffff; color: #0f172a;")
        self.resize(520, 480)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Add New Audit Client & Statutory Profile")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; letter-spacing: -0.4px; background: transparent; background-color: transparent;")
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
            input_field.setStyleSheet("padding: 8px 12px; border: 1px solid #e1e8f4; border-radius: 8px; color: #0f172a; background-color: #ffffff;")
            
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Client Legal Name *</b>"), self.name_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Entity Type</b>"), self.entity_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>GSTIN Number</b>"), self.gst_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>PAN Number</b>"), self.pan_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>CIN Number</b>"), self.cin_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Managing Director / KMP</b>"), self.kmp_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Industry Sector</b>"), self.industry_input)
        
        layout.addWidget(form_frame)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setStyleSheet("""
            QPushButton { padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: 500; }
            QPushButton[text="OK"] { background-color: #0284c7; color: white; border: none; font-weight: 600; }
            QPushButton[text="Cancel"] { background-color: #ffffff; color: #334155; border: 1px solid #e1e8f4; }
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
    def __init__(self, parent=None, client_id=None):
        super().__init__(parent)
        self.setWindowTitle("Initialize Statutory Audit Project")
        self.setStyleSheet("background-color: #ffffff; color: #0f172a;")
        self.resize(460, 320)
        self.client_id = client_id
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Create Statutory Audit Engagement")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; letter-spacing: -0.4px; background: transparent; background-color: transparent;")
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        
        self.client_combo = QComboBox()
        self.populate_clients()
        
        self.fy_combo = QComboBox()
        self.fy_combo.addItems(["2025-26", "2024-25", "2023-24", "2022-23"])
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Statutory Audit (Companies Act)", "Tax Audit (Sec 44AB)", "GST Audit", "Internal Financial Controls (IFCoFR)", "Limited Review (Quarterly)"])
        
        for cb in [self.client_combo, self.fy_combo, self.type_combo]:
            cb.setStyleSheet("padding: 8px; border: 1px solid #e1e8f4; border-radius: 6px; background-color: #ffffff; color: #0f172a;")
            
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Audit Client *</b>"), self.client_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Financial Year (FY) *</b>"), self.fy_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Audit Engagement Type *</b>"), self.type_combo)
        
        layout.addWidget(form_frame)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setStyleSheet("""
            QPushButton { padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: 500; }
            QPushButton[text="OK"] { background-color: #0284c7; color: white; border: none; font-weight: 600; }
            QPushButton[text="Cancel"] { background-color: #ffffff; color: #334155; border: 1px solid #e1e8f4; }
        """)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def populate_clients(self):
        try:
            with SessionLocal() as session:
                clients = session.query(Client).all()
                for c in clients:
                    gst = getattr(c, 'gst_number', getattr(c, 'gstin', None))
                    pan = getattr(c, 'pan_number', getattr(c, 'pan', None))
                    reg = gst or pan or 'No Reg'
                    self.client_combo.addItem(f"{c.name} ({reg})", c.id)
                if self.client_id:
                    index = self.client_combo.findData(self.client_id)
                    if index >= 0:
                        self.client_combo.setCurrentIndex(index)
        except SQLAlchemyError:
            pass

class ClientManagementWidget(QWidget):
    """Statutory Master Client Register & Engagement Management Workspace."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f0f6ff;")
        self.selected_client_id = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("clientsHeader")
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("Client CRM & Statutory Profile Vault")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; letter-spacing: -0.4px; border: none; background: transparent; background-color: transparent;")
        subtitle = QLabel("Client Master Register, Statutory Registrations & Engagement History")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none; background: transparent; background-color: transparent;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()
        
        btn_add = QPushButton("+ Add New Client")
        btn_add.setObjectName("primaryBtn")
        btn_add.setToolTip("Register a new client entity into statutory master vault")
        btn_add.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn_add.setStyleSheet("""
            QPushButton#primaryBtn {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton#primaryBtn:hover { background-color: #0369a1; }
        """)
        btn_add.clicked.connect(self.open_add_client_dialog)
        
        btn_new_audit = QPushButton("+ New Audit Project")
        btn_new_audit.setObjectName("secondaryBtn")
        btn_new_audit.setToolTip("Initialize a new statutory audit engagement for client")
        btn_new_audit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn_new_audit.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #0284c7;
                font-size: 13px;
                font-weight: 600;
                border: 1px solid #e1e8f4;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #f8fafc; border-color: #0284c7; }
        """)
        btn_new_audit.clicked.connect(self.open_create_audit_dialog)
        
        h_layout.addWidget(btn_add)
        h_layout.addSpacing(8)
        h_layout.addWidget(btn_new_audit)
        main_layout.addWidget(header)
        
        # 2. Main Splitter View
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e1e8f4; }")
        
        # Left Pane: Client Table
        left_container = QFrame()
        left_container.setObjectName("clientsLeftPane")
        left_container.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e1e8f4;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(16, 16, 16, 16)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Client Name, PAN, or GSTIN...")
        self.search_input.setToolTip("Search client master records by legal name, GSTIN, or PAN")
        self.search_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.search_input.setStyleSheet("padding: 8px 12px; border: 1px solid #e1e8f4; border-radius: 8px; background-color: #ffffff; color: #0f172a;")
        self.search_input.textChanged.connect(self.filter_clients)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        self.table = QTableWidget(0, 3)
        self.table.setToolTip("Client Master Register Table")
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.setHorizontalHeaderLabels(["Client Legal Name", "GSTIN / PAN", "Industry"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget, QTableWidget::viewport { border: 1px solid #e1e8f4; gridline-color: #f0f6ff; background: #ffffff; color: #0f172a; border-radius: 10px; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: 600; font-size: 10px; letter-spacing: 0.8px; padding: 10px; border: none; border-bottom: 1px solid #e1e8f4; }
            QTableWidget::item { color: #0f172a; }
            QTableWidget::item:selected { background-color: rgba(2, 132, 199, 0.12); color: #0284c7; font-weight: 600; }
        """)
        self.table.itemSelectionChanged.connect(self.on_client_selected)
        left_layout.addWidget(self.table)
        
        splitter.addWidget(left_container)
        
        # Right Pane: 4-Tab Client Details Vault
        right_container = QFrame()
        right_container.setStyleSheet("background-color: #f0f6ff;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e8f4; background: #ffffff; border-radius: 8px; }
            QTabBar::tab { background: #e0f2fe; color: #64748b; padding: 8px 16px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
            QTabBar::tab:selected { background: #0284c7; color: white; }
        """)
        
        self.tabs.addTab(self._create_profile_tab(), "Statutory Profile")
        self.tabs.addTab(self._create_history_tab(), "Engagement History")
        self.tabs.addTab(self._create_paf_tab(), "Permanent Audit File (PAF)")
        
        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_container)
        
        splitter.setSizes([450, 750])
        main_layout.addWidget(splitter)
        
        self.load_clients()

    def _create_profile_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)
        w_layout.setSpacing(12)
        
        card = QFrame()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setObjectName("clientFormCard")
        card.setStyleSheet("background-color: #ffffff; border: 1px solid #e1e8f4; border-radius: 12px; padding: 16px;")
        f_layout = QFormLayout(card)
        f_layout.setSpacing(10)
        
        self.edit_name = QLineEdit()
        self.edit_gst = QLineEdit()
        self.edit_pan = QLineEdit()
        self.edit_cin = QLineEdit()
        self.edit_entity = QLineEdit()
        self.edit_industry = QLineEdit()

        for f in [self.edit_name, self.edit_gst, self.edit_pan, self.edit_cin, self.edit_entity, self.edit_industry]:
            f.setStyleSheet("padding: 8px 12px; border: 1px solid #e1e8f4; border-radius: 8px; background-color: #ffffff; color: #0f172a;")

        f_layout.addRow(QLabel("<b style='color:#0f172a; border: none; background: transparent;'>Legal Entity Name</b>"), self.edit_name)
        f_layout.addRow(QLabel("<b style='color:#0f172a; border: none; background: transparent;'>GSTIN Registration</b>"), self.edit_gst)
        f_layout.addRow(QLabel("<b style='color:#0f172a; border: none; background: transparent;'>PAN Identification</b>"), self.edit_pan)
        f_layout.addRow(QLabel("<b style='color:#0f172a; border: none; background: transparent;'>CIN Registration</b>"), self.edit_cin)
        f_layout.addRow(QLabel("<b style='color:#0f172a; border: none; background: transparent;'>Structure / Entity Type</b>"), self.edit_entity)
        f_layout.addRow(QLabel("<b style='color:#0f172a; border: none; background: transparent;'>Industry Sector</b>"), self.edit_industry)
        
        w_layout.addWidget(card)
        
        btn_update = QPushButton("Update Client Statutory Info")
        btn_update.setObjectName("primaryBtn")
        btn_update.setStyleSheet("background-color: #0284c7; color: white; padding: 10px; border-radius: 8px; font-weight: bold; border: none;")
        btn_update.clicked.connect(self.update_client_profile)
        w_layout.addWidget(btn_update)
        
        w_layout.addStretch()
        return widget

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(16, 16, 16, 16)
        
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Financial Year", "Audit Type", "Status", "Risk Level"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setStyleSheet("""
            QTableWidget, QTableWidget::viewport { border: 1px solid #334155; background: #1e293b; color: #f8fafc; border-radius: 8px; }
            QHeaderView::section { background-color: #0f172a; color: #94a3b8; font-size: 10px; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #334155; }
            QTableWidget::item { color: #f8fafc; }
        """)
        l.addWidget(self.history_table)
        return widget

    def _create_paf_tab(self) -> QWidget:
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(16, 16, 16, 16)
        
        lbl = QLabel("Permanent Audit File (PAF) Master Documents")
        lbl.setStyleSheet("font-weight: 700; color: #f8fafc; font-size: 14px; margin-bottom: 8px; background: transparent;")
        l.addWidget(lbl)
        
        self.paf_text = QTextEdit()
        self.paf_text.setReadOnly(True)
        self.paf_text.setStyleSheet("border: 1px solid #334155; border-radius: 8px; background-color: #0f172a; color: #f8fafc; padding: 12px;")
        self.paf_text.setText("Permanent Audit File (PAF) Documents:\n\n1. Certificate of Incorporation & MoA / AoA\n2. Board Resolutions & Authorized Signatories\n3. Tax Registrations (GST, PAN, TAN)\n4. Property Deeds & Lease Agreements")
        l.addWidget(self.paf_text)
        return widget

    def load_clients(self):
        try:
            with SessionLocal() as session:
                clients = session.query(Client).all()
                self.table.setRowCount(len(clients))
                for idx, c in enumerate(clients):
                    item_name = QTableWidgetItem(c.name)
                    item_name.setData(Qt.ItemDataRole.UserRole, c.id)
                    gst = getattr(c, 'gst_number', getattr(c, 'gstin', None))
                    pan = getattr(c, 'pan_number', getattr(c, 'pan', None))
                    item_reg = QTableWidgetItem(gst or pan or "N/A")
                    item_ind = QTableWidgetItem(c.industry or "General")
                    
                    self.table.setItem(idx, 0, item_name)
                    self.table.setItem(idx, 1, item_reg)
                    self.table.setItem(idx, 2, item_ind)
        except SQLAlchemyError as e:
            self.error_widget = ErrorStateWidget("Database Connection Error", str(e))

    def filter_clients(self, text):
        query = text.strip().lower()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().lower() if self.table.item(row, 0) else ""
            reg = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ""
            match = query in name or query in reg
            self.table.setRowHidden(row, not match)

    def on_client_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows: return
        
        row = selected_rows[0].row()
        client_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.selected_client_id = client_id
        
        try:
            with SessionLocal() as session:
                client = session.query(Client).filter_by(id=client_id).first()
                if client:
                    self.edit_name.setText(client.name or "")
                    gst = getattr(client, 'gst_number', getattr(client, 'gstin', ""))
                    pan = getattr(client, 'pan_number', getattr(client, 'pan', ""))
                    self.edit_gst.setText(gst or "")
                    self.edit_pan.setText(pan or "")
                    self.edit_cin.setText(client.cin or "")
                    self.edit_entity.setText(getattr(client, 'entity_type', "Private Limited Company") or "")
                    self.edit_industry.setText(client.industry or "")
                    
                    projects = session.query(AuditProject).filter_by(client_id=client.id).all()
                    self.history_table.setRowCount(len(projects))
                    for p_idx, p in enumerate(projects):
                        self.history_table.setItem(p_idx, 0, QTableWidgetItem(p.financial_year))
                        self.history_table.setItem(p_idx, 1, QTableWidgetItem(p.audit_type or "Statutory Audit"))
                        self.history_table.setItem(p_idx, 2, QTableWidgetItem(p.status))
                        self.history_table.setItem(p_idx, 3, QTableWidgetItem(p.risk_level))
        except SQLAlchemyError:
            pass

    def update_client_profile(self):
        if not self.selected_client_id:
            QMessageBox.warning(self, "No Selection", "Please select a client from the left register table.")
            return
            
        try:
            with SessionLocal() as session:
                client = session.query(Client).filter_by(id=self.selected_client_id).first()
                if client:
                    client.name = self.edit_name.text().strip()
                    val_gst = self.edit_gst.text().strip()
                    val_pan = self.edit_pan.text().strip()
                    if hasattr(client, 'gst_number'): client.gst_number = val_gst
                    if hasattr(client, 'gstin'): client.gstin = val_gst
                    if hasattr(client, 'pan_number'): client.pan_number = val_pan
                    if hasattr(client, 'pan'): client.pan = val_pan
                    client.cin = self.edit_cin.text().strip()
                    if hasattr(client, 'entity_type'): client.entity_type = self.edit_entity.text().strip()
                    client.industry = self.edit_industry.text().strip()
                    session.commit()
                    QMessageBox.information(self, "Profile Updated", f"Statutory profile for {client.name} updated successfully.")
                    self.load_clients()
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update client profile: {e}")

    def open_add_client_dialog(self):
        dialog = AddClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                with SessionLocal() as session:
                    gst_val = dialog.gst_input.text().strip() or None
                    pan_val = dialog.pan_input.text().strip() or None
                    new_client = Client(
                        name=dialog.name_input.text().strip(),
                        gst_number=gst_val,
                        pan_number=pan_val,
                        cin=dialog.cin_input.text().strip() or None,
                        industry=dialog.industry_input.text().strip() or "General"
                    )
                    session.add(new_client)
                    session.commit()
                    QMessageBox.information(self, "Client Created", f"Client {new_client.name} successfully registered in master vault.")
                    self.load_clients()
            except SQLAlchemyError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add client: {e}")

    def open_create_audit_dialog(self):
        dialog = CreateAuditProjectDialog(self, client_id=self.selected_client_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                with SessionLocal() as session:
                    client_id = dialog.client_combo.currentData()
                    new_project = AuditProject(
                        client_id=client_id,
                        financial_year=dialog.fy_combo.currentText(),
                        audit_type=dialog.type_combo.currentText(),
                        risk_level=dialog.risk_combo.currentText(),
                        status="Planning"
                    )
                    session.add(new_project)
                    session.commit()
                    QMessageBox.information(self, "Audit Created", "New statutory audit project initialized successfully.")
                    self.load_clients()
            except SQLAlchemyError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to initialize audit project: {e}")
