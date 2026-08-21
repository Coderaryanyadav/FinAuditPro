"""
Client Workspace & Statutory Master Vault for FinAuditPro.
Redesigned into a professional Client Workspace featuring:
1. Client Directory with Search, Filter & Entity Type badges
2. High-density Client Workspace Profile (Read-Only Default + Edit Mode)
3. Primary Action Bar ([+ Create Audit], [Open Current Audit →], [Edit Profile])
4. Multi-Year Audit Engagement History Timeline with direct audit launch
5. Permanent Audit File (PAF) Master Document Vault
"""

import re
import logging
from typing import List, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QLineEdit, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QSplitter, QDialog, 
                               QDialogButtonBox, QFormLayout, QMessageBox, QComboBox, 
                               QTabWidget, QTextEdit, QScrollArea, QListWidget, QListWidgetItem, QStackedWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from database.database import get_session
from database.models import Client, AuditProject, Engagement, Document, Finding, WorkingPaper
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from .icons import get_app_icon, get_app_pixmap
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ==============================================================================
# DIALOGS
# ==============================================================================

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Client Entity")
        self.setStyleSheet("background-color: #FFFFFF; color: #111827;")
        self.resize(520, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Add New Audit Client Entity")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 8px; letter-spacing: -0.2px; border: none;")
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Acme Corp India Ltd")
        
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
            input_field.setStyleSheet("padding: 8px 12px; border: 1px solid #e1e8f4; border-radius: 6px; color: #0f172a; background-color: #ffffff; font-size: 12px;")
            
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Client Legal Name *</b>"), self.name_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Entity Type</b>"), self.entity_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>GSTIN Number</b>"), self.gst_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>PAN Number</b>"), self.pan_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>CIN Number</b>"), self.cin_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Managing Director / KMP</b>"), self.kmp_input)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Industry Sector</b>"), self.industry_input)
        
        layout.addWidget(form_frame)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
        self.setWindowTitle("Initialize Statutory Audit Engagement")
        self.setStyleSheet("background-color: #ffffff; color: #0f172a;")
        self.resize(480, 440)
        self.client_id = client_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Create Statutory Audit Engagement")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 8px; letter-spacing: -0.4px; border: none;")
        layout.addWidget(title)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)

        self.client_combo = QComboBox()
        self.populate_clients()

        self.fy_combo = QComboBox()
        self.fy_combo.addItems(["2025-26", "2024-25", "2023-24", "2022-23"])

        self.audit_type_combo = QComboBox()
        self.audit_type_combo.addItems([
            "Statutory Audit (Companies Act)",
            "Tax Audit (Sec 44AB)",
            "GST Audit",
            "Internal Financial Controls (IFCoFR)",
            "Limited Review (Quarterly)",
        ])
        self.type_combo = self.audit_type_combo # Alias for backwards compatibility

        self.stage_combo = QComboBox()
        self.stage_combo.addItems(["Planning", "Execution", "Reporting", "Completed"])

        self.risk_combo = QComboBox()
        self.risk_combo.addItems(["Low", "Medium", "High"])
        self.risk_combo.setCurrentText("Medium")

        _cb_style = "padding: 8px; border: 1px solid #e1e8f4; border-radius: 6px; background-color: #ffffff; color: #0f172a; font-size: 12px;"
        for cb in [self.client_combo, self.fy_combo, self.audit_type_combo, self.stage_combo, self.risk_combo]:
            cb.setStyleSheet(_cb_style)

        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Audit Client *</b>"), self.client_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Financial Year (FY) *</b>"), self.fy_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Audit Engagement Type *</b>"), self.audit_type_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Stage</b>"), self.stage_combo)
        form_layout.addRow(QLabel("<b style='color:#0f172a;'>Risk Level</b>"), self.risk_combo)

        layout.addWidget(form_frame)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setStyleSheet("""
            QPushButton { padding: 8px 18px; border-radius: 6px; font-size: 12px; font-weight: 600; }
            QPushButton[text="OK"] { background-color: #0284c7; color: white; border: none; }
            QPushButton[text="Cancel"] { background-color: #ffffff; color: #334155; border: 1px solid #e1e8f4; }
        """)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def populate_clients(self):
        try:
            with get_session() as session:
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

# ==============================================================================
# MAIN CLIENT WORKSPACE WIDGET
# ==============================================================================

class ClientManagementWidget(QFrame):
    """Professional Client Workspace & Statutory Vault Widget for FinAuditPro."""

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("appBg")
        self.selected_client_id = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(64)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setObjectName("contentHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("Clients Workspace")
        title.setObjectName("heroTitle")
        subtitle = QLabel("Manage statutory client profiles, engagement timelines, and permanent audit files.")
        subtitle.setObjectName("heroSub")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()
        
        btn_add = QPushButton(" + New Client")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                padding: 7px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        btn_add.clicked.connect(self.open_add_client_dialog)
        
        btn_new_audit = QPushButton(" + New Audit Project")
        btn_new_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_audit.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #0284c7;
                font-size: 12px;
                font-weight: 700;
                border: 1px solid #bae6fd;
                border-radius: 6px;
                padding: 7px 16px;
            }
            QPushButton:hover { background-color: #e0f2fe; }
        """)
        btn_new_audit.clicked.connect(self.open_create_audit_dialog)
        
        h_layout.addWidget(btn_add)
        h_layout.addSpacing(8)
        h_layout.addWidget(btn_new_audit)
        main_layout.addWidget(header)
        
        # 2. Main Splitter View
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Pane: Client Directory List
        left_container = QFrame()
        left_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        left_container.setObjectName("leftContainer")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)
        
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchField")
        self.search_input.setPlaceholderText("Search clients by name, PAN, GSTIN, CIN...")
        self.search_input.textChanged.connect(self.filter_clients)
        search_row.addWidget(self.search_input)
        left_layout.addLayout(search_row)

        self.client_list = QListWidget()
        self.client_list.setObjectName("clientListWidget")
        self.client_list.itemSelectionChanged.connect(self.on_client_selected)
        left_layout.addWidget(self.client_list)
        
        splitter.addWidget(left_container)
        
        # Right Pane: Client Workspace Profile
        self.right_container = QFrame()
        self.right_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.right_container.setObjectName("appBg")
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(20, 20, 20, 20)
        self.right_layout.setSpacing(16)
        
        self.workspace_stack = QStackedWidget()
        self.workspace_stack.addWidget(self._build_empty_client_state())
        self.workspace_stack.addWidget(self._build_client_profile_workspace())
        
        self.right_layout.addWidget(self.workspace_stack)
        splitter.addWidget(self.right_container)
        
        splitter.setSizes([420, 780])
        main_layout.addWidget(splitter)
        
        self.is_editing_profile = False
        self.load_clients()

    def _build_empty_client_state(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty = EmptyStateWidget(
            title="No Client Selected",
            description="Select a client from the left directory to view its statutory profile, engagement timeline, and permanent audit file (PAF)."
        )
        l.addWidget(empty)
        return w

    def _build_client_profile_workspace(self) -> QWidget:
        w = QWidget()
        w_layout = QVBoxLayout(w)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.setSpacing(14)

        # 1. Profile Header Card
        self.profile_header_card = QFrame()
        self.profile_header_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.profile_header_card.setObjectName("contentCard")
        ph_layout = QVBoxLayout(self.profile_header_card)
        ph_layout.setSpacing(10)

        top_r = QHBoxLayout()
        v_info = QVBoxLayout()
        v_info.setSpacing(2)
        
        self.lbl_client_name = QLabel("Client Legal Name")
        self.lbl_client_name.setObjectName("heroTitle")
        self.lbl_client_sub = QLabel("Private Limited Company • Technology Sector")
        self.lbl_client_sub.setObjectName("heroSub")
        
        v_info.addWidget(self.lbl_client_name)
        v_info.addWidget(self.lbl_client_sub)
        
        top_r.addLayout(v_info)
        top_r.addStretch()
        
        self.lbl_client_badge = QLabel("Active Client")
        self.lbl_client_badge.setStyleSheet("font-size: 11px; font-weight: 800; color: #047857; background: #dcfce7; padding: 4px 12px; border-radius: 10px; border: 1px solid #bbf7d0;")
        top_r.addWidget(self.lbl_client_badge, alignment=Qt.AlignmentFlag.AlignTop)
        ph_layout.addLayout(top_r)

        # Identifiers row
        id_row = QHBoxLayout()
        id_row.setSpacing(16)
        
        self.lbl_pan_id = QLabel("PAN: —")
        self.lbl_gst_id = QLabel("GSTIN: —")
        self.lbl_cin_id = QLabel("CIN: —")
        
        _id_style = "font-size: 11px; font-weight: 600; color: #475569; background: #f8fafc; padding: 4px 10px; border-radius: 6px; border: 1px solid #e1e8f4;"
        for lbl in [self.lbl_pan_id, self.lbl_gst_id, self.lbl_cin_id]:
            lbl.setStyleSheet(_id_style)
            id_row.addWidget(lbl)
        id_row.addStretch()
        ph_layout.addLayout(id_row)

        # Action Buttons Row
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.btn_create_audit_for_client = QPushButton("+ Create Audit Engagement")
        self.btn_create_audit_for_client.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_create_audit_for_client.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 14px;
                border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.btn_create_audit_for_client.clicked.connect(self.open_create_audit_dialog)

        self.btn_open_current_audit = QPushButton("Open Current Audit →")
        self.btn_open_current_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_current_audit.setStyleSheet("""
            QPushButton {
                background-color: #e0f2fe;
                color: #0284c7;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 14px;
                border: 1px solid #bae6fd;
            }
            QPushButton:hover { background-color: #bae6fd; }
        """)
        self.btn_open_current_audit.clicked.connect(self._open_active_client_engagement)

        self.btn_toggle_edit = QPushButton("Edit Profile")
        self.btn_toggle_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_edit.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                padding: 6px 14px;
                border: 1px solid #cbd5e1;
            }
            QPushButton:hover { background-color: #f8fafc; border-color: #0284c7; color: #0284c7; }
        """)
        self.btn_toggle_edit.clicked.connect(self.toggle_edit_mode)

        action_row.addWidget(self.btn_create_audit_for_client)
        action_row.addWidget(self.btn_open_current_audit)
        action_row.addWidget(self.btn_toggle_edit)
        action_row.addStretch()
        ph_layout.addLayout(action_row)

        w_layout.addWidget(self.profile_header_card)
        apply_shadow(self.profile_header_card, blur=12, dx=0, dy=2, alpha=10)

        # 2. Tabs Vault
        self.tabs = QTabWidget()
        self.tabs.setObjectName("clientTabsWidget")
        
        self.tabs.addTab(self._create_profile_tab(), "Statutory Profile")
        self.tabs.addTab(self._create_history_tab(), "Audit Engagements Timeline")
        self.tabs.addTab(self._create_paf_tab(), "Permanent Audit File (PAF)")
        
        w_layout.addWidget(self.tabs)
        return w

    def _create_profile_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(18, 18, 18, 18)
        w_layout.setSpacing(14)

        # Stacked view: 0 = Read Only Display, 1 = Form Edit View
        self.profile_stack = QStackedWidget()

        # Read-Only View
        read_widget = QWidget()
        rl = QVBoxLayout(read_widget)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)

        read_card = QFrame()
        read_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        read_card.setObjectName("contentCard")
        fl = QFormLayout(read_card)
        fl.setSpacing(10)

        self.disp_name = QLabel("—")
        self.disp_gst = QLabel("—")
        self.disp_pan = QLabel("—")
        self.disp_cin = QLabel("—")
        self.disp_entity = QLabel("—")
        self.disp_industry = QLabel("—")

        fl.addRow(QLabel("Legal Entity Name:"), self.disp_name)
        fl.addRow(QLabel("GSTIN Number:"), self.disp_gst)
        fl.addRow(QLabel("PAN Number:"), self.disp_pan)
        fl.addRow(QLabel("CIN Number:"), self.disp_cin)
        fl.addRow(QLabel("Structure / Entity Type:"), self.disp_entity)
        fl.addRow(QLabel("Industry Sector:"), self.disp_industry)

        rl.addWidget(read_card)
        rl.addStretch()

        # Edit Form View
        edit_widget = QWidget()
        el = QVBoxLayout(edit_widget)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(12)

        edit_card = QFrame()
        edit_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        edit_card.setObjectName("contentCard")
        efl = QFormLayout(edit_card)
        efl.setSpacing(10)

        self.edit_name = QLineEdit()
        self.edit_gst = QLineEdit()
        self.edit_pan = QLineEdit()
        self.edit_cin = QLineEdit()
        self.edit_entity = QLineEdit()
        self.edit_industry = QLineEdit()

        for f in [self.edit_name, self.edit_gst, self.edit_pan, self.edit_cin, self.edit_entity, self.edit_industry]:
            f.setObjectName("inputField")

        efl.addRow(QLabel("Legal Entity Name *"), self.edit_name)
        efl.addRow(QLabel("GSTIN Registration"), self.edit_gst)
        efl.addRow(QLabel("PAN Identification"), self.edit_pan)
        efl.addRow(QLabel("CIN Registration"), self.edit_cin)
        efl.addRow(QLabel("Structure / Entity Type"), self.edit_entity)
        efl.addRow(QLabel("Industry Sector"), self.edit_industry)

        el.addWidget(edit_card)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Changes")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.update_client_profile)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.toggle_edit_mode)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        el.addLayout(btn_row)
        el.addStretch()

        self.profile_stack.addWidget(read_widget)
        self.profile_stack.addWidget(edit_widget)

        w_layout.addWidget(self.profile_stack)
        return widget

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(18, 18, 18, 18)
        
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["FINANCIAL YEAR", "AUDIT TYPE", "STATUS", "RISK LEVEL", "ACTION"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setObjectName("dataTable")
        l.addWidget(self.history_table)
        return widget

    def _create_paf_tab(self) -> QWidget:
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(10)
        
        lbl = QLabel("Permanent Audit File (PAF) Master Documents")
        lbl.setObjectName("heroSub")
        l.addWidget(lbl)
        
        self.paf_table = QTableWidget(0, 3)
        self.paf_table.setHorizontalHeaderLabels(["DOCUMENT CATEGORY", "FILE NAME / REF", "STATUS"])
        self.paf_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.paf_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.paf_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.paf_table.verticalHeader().setVisible(False)
        self.paf_table.setObjectName("dataTable")
        l.addWidget(self.paf_table)
        return widget

    def load_clients(self):
        self.client_list.clear()
        try:
            with get_session() as session:
                clients = session.query(Client).order_by(Client.id.asc()).all()
                for c in clients:
                    gst = getattr(c, 'gst_number', getattr(c, 'gstin', None))
                    pan = getattr(c, 'pan_number', getattr(c, 'pan', None))
                    reg = gst or pan or "No Tax ID"
                    entity = getattr(c, 'entity_type', "Private Limited") or "Private Limited"

                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, c.id)
                    item.setText(f"{c.name}\n{entity} • {reg}")
                    self.client_list.addItem(item)

                if self.client_list.count() > 0:
                    self.client_list.setCurrentRow(0)
                    self.workspace_stack.setCurrentIndex(1)
                else:
                    self.workspace_stack.setCurrentIndex(0)
        except SQLAlchemyError as e:
            logger.warning(f"Error loading clients: {e}")

    def filter_clients(self, text):
        query = text.strip().lower()
        for i in range(self.client_list.count()):
            item = self.client_list.item(i)
            match = query in item.text().lower()
            item.setHidden(not match)

    def toggle_edit_mode(self):
        self.is_editing_profile = not self.is_editing_profile
        self.profile_stack.setCurrentIndex(1 if self.is_editing_profile else 0)
        self.btn_toggle_edit.setText("Cancel Edit" if self.is_editing_profile else "Edit Profile")

    def on_client_selected(self):
        selected_items = self.client_list.selectedItems()
        if not selected_items:
            self.workspace_stack.setCurrentIndex(0)
            return

        client_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.selected_client_id = client_id
        self.workspace_stack.setCurrentIndex(1)

        try:
            with get_session() as session:
                client = session.query(Client).filter_by(id=client_id).first()
                if client:
                    gst = getattr(client, 'gst_number', getattr(client, 'gstin', "")) or "—"
                    pan = getattr(client, 'pan_number', getattr(client, 'pan', "")) or "—"
                    cin = getattr(client, 'cin', "") or "—"
                    entity = getattr(client, 'entity_type', "Private Limited Company") or "Private Limited Company"
                    industry = getattr(client, 'industry', "Technology") or "Technology"

                    # Header
                    self.lbl_client_name.setText(client.name)
                    self.lbl_client_sub.setText(f"{entity} • {industry} Sector")
                    self.lbl_pan_id.setText(f"PAN: {pan}")
                    self.lbl_gst_id.setText(f"GSTIN: {gst}")
                    self.lbl_cin_id.setText(f"CIN: {cin}")

                    # Read Only Display
                    self.disp_name.setText(client.name)
                    self.disp_gst.setText(gst)
                    self.disp_pan.setText(pan)
                    self.disp_cin.setText(cin)
                    self.disp_entity.setText(entity)
                    self.disp_industry.setText(industry)

                    # Edit Inputs
                    self.edit_name.setText(client.name or "")
                    self.edit_gst.setText("" if gst == "—" else gst)
                    self.edit_pan.setText("" if pan == "—" else pan)
                    self.edit_cin.setText("" if cin == "—" else cin)
                    self.edit_entity.setText(entity)
                    self.edit_industry.setText(industry)

                    # Engagements History Timeline
                    projects = session.query(AuditProject).filter_by(client_id=client.id).order_by(AuditProject.id.desc()).all()
                    self.history_table.setRowCount(len(projects))
                    for p_idx, p in enumerate(projects):
                        self.history_table.setItem(p_idx, 0, QTableWidgetItem(p.financial_year or "2025-26"))
                        self.history_table.setItem(p_idx, 1, QTableWidgetItem(getattr(p, 'audit_type', 'Statutory Audit') or "Statutory Audit"))
                        self.history_table.setItem(p_idx, 2, QTableWidgetItem(p.status or "In Progress"))
                        self.history_table.setItem(p_idx, 3, QTableWidgetItem(p.risk_level or "Low"))
                        
                        btn_open = QPushButton("Open Audit →")
                        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
                        btn_open.setStyleSheet("font-size: 11px; font-weight: 700; color: #0284c7; background: #e0f2fe; border: 1px solid #bae6fd; border-radius: 4px; padding: 2px 8px;")
                        proj_id = p.id
                        btn_open.clicked.connect(lambda checked=False, pid=proj_id: self._open_specific_audit_project(pid))
                        self.history_table.setCellWidget(p_idx, 4, btn_open)

                    # PAF Master Documents
                    docs = session.query(Document).join(Engagement).filter(Engagement.client_id == client.id).all()
                    standard_paf = [
                        ("Certificate of Incorporation & MoA / AoA", "Verified"),
                        ("Tax Registrations (GSTIN, PAN, TAN)", "Verified"),
                        ("Board Resolutions & Key KMP Signatories", "Verified"),
                        ("Permanent Lease Agreements & Property Deeds", "Verified"),
                    ]
                    self.paf_table.setRowCount(len(standard_paf) + len(docs))
                    for d_idx, (cat, stat) in enumerate(standard_paf):
                        self.paf_table.setItem(d_idx, 0, QTableWidgetItem(cat))
                        self.paf_table.setItem(d_idx, 1, QTableWidgetItem(f"{client.name} Master Vault Ref #{d_idx+101}"))
                        self.paf_table.setItem(d_idx, 2, QTableWidgetItem(stat))
                    
                    for d_idx, doc in enumerate(docs, start=len(standard_paf)):
                        self.paf_table.setItem(d_idx, 0, QTableWidgetItem(getattr(doc, 'category', 'Audit File') or "Audit File"))
                        self.paf_table.setItem(d_idx, 1, QTableWidgetItem(doc.filename))
                        self.paf_table.setItem(d_idx, 2, QTableWidgetItem("Uploaded"))

        except SQLAlchemyError as e:
            logger.warning(f"Error loading client profile: {e}")

    def update_client_profile(self):
        if not self.selected_client_id:
            return
            
        try:
            with get_session() as session:
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
                    
                    self.is_editing_profile = False
                    self.profile_stack.setCurrentIndex(0)
                    self.btn_toggle_edit.setText("Edit Profile")
                    self.load_clients()
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update client profile: {e}")

    def open_add_client_dialog(self):
        dialog = AddClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                with get_session() as session:
                    gst_val = dialog.gst_input.text().strip() or None
                    pan_val = dialog.pan_input.text().strip() or None
                    new_client = Client(
                        name=dialog.name_input.text().strip(),
                        gst_number=gst_val,
                        pan_number=pan_val,
                        cin=dialog.cin_input.text().strip() or None,
                        industry=dialog.industry_input.text().strip() or "Technology"
                    )
                    if hasattr(new_client, 'entity_type'):
                        new_client.entity_type = dialog.entity_combo.currentText()
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
                with get_session() as session:
                    client_id = dialog.client_combo.currentData()
                    new_project = AuditProject(
                        client_id=client_id,
                        financial_year=dialog.fy_combo.currentText(),
                        audit_type=dialog.audit_type_combo.currentText(),
                        risk_level=dialog.risk_combo.currentText(),
                        status="Planning"
                    )
                    session.add(new_project)
                    session.commit()
                    QMessageBox.information(self, "Audit Created", "New statutory audit project initialized successfully.")
                    self.load_clients()
                    self.on_client_selected()
            except SQLAlchemyError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to initialize audit project: {e}")

    def _open_active_client_engagement(self):
        if not self.selected_client_id:
            return
        parent_dash = self.window()
        if parent_dash and hasattr(parent_dash, 'client_selector'):
            idx = parent_dash.client_selector.findData(self.selected_client_id)
            if idx >= 0:
                parent_dash.client_selector.setCurrentIndex(idx)
            if hasattr(parent_dash, 'btn_upload'):
                parent_dash.btn_upload.click()

    def _open_specific_audit_project(self, project_id: int):
        parent_dash = self.window()
        if parent_dash and hasattr(parent_dash, 'client_selector'):
            idx = parent_dash.client_selector.findData(project_id)
            if idx >= 0:
                parent_dash.client_selector.setCurrentIndex(idx)
            if hasattr(parent_dash, 'btn_upload'):
                parent_dash.btn_upload.click()
