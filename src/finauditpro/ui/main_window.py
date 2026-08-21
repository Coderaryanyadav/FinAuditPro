"""
Main Application Shell Window for FinAuditPro.
Enterprise Audit Operating System with Sidebar Navigation, Context Header, and Stacked View Workspace.
"""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.ui.dialogs.engagement_dialog import EngagementDialog
from finauditpro.ui.dialogs.login_dialog import LoginDialog
from finauditpro.ui.styles import GLOBAL_QSS
from finauditpro.ui.views.ai_assistant_view import AIAssistantView
from finauditpro.ui.views.archival_view import ArchivalView
from finauditpro.ui.views.audit_matrix_view import AuditMatrixView
from finauditpro.ui.views.client_view import ClientView
from finauditpro.ui.views.compliance_view import ComplianceView
from finauditpro.ui.views.dashboard_view import DashboardView
from finauditpro.ui.views.document_view import DocumentView
from finauditpro.ui.views.engagement_view import EngagementView
from finauditpro.ui.views.financial_data_view import FinancialDataView
from finauditpro.ui.views.firm_view import FirmView
from finauditpro.ui.views.gst_verification_view import GSTVerificationView
from finauditpro.ui.views.report_view import ReportView
from finauditpro.ui.views.roll_forward_view import RollForwardView
from finauditpro.ui.views.settings_view import SettingsView
from finauditpro.ui.views.working_paper_view import WorkingPaperView

NAV_ITEMS = [
    ("btn_dashboard", "Dashboard", "WORKSPACE"), ("btn_firms", "Audit Firms", "WORKSPACE"),
    ("btn_clients", "Clients", "WORKSPACE"), ("btn_engagements", "Engagements", "WORKSPACE"),
    ("btn_documents", "Documents", "FINANCIAL"), ("btn_financial_data", "Financial Statements", "FINANCIAL"),
    ("btn_gst", "GST Reconciliation", "FINANCIAL"), ("btn_compliance", "Statutory Compliance", "FINANCIAL"),
    ("btn_audit_matrix", "Audit Matrix", "ANALYSIS"), ("btn_ai_assistant", "AI Copilot", "ANALYSIS"),
    ("btn_working_papers", "Working Papers", "AUDIT WORKFLOW"), ("btn_reports", "Reports", "AUDIT WORKFLOW"),
    ("btn_archival", "File Archival", "SYSTEM"), ("btn_roll_forward", "Roll-Forward", "SYSTEM"),
    ("btn_settings", "Settings", "SYSTEM"),
]

class MainWindow(QMainWindow):
    """Main Application Shell Window for FinAuditPro Audit Command Center."""

    def __init__(self, firm_service: Any = None, client_service: Any = None, engagement_service: Any = None, document_service: Any = None, financial_data_service: Any = None, audit_matrix_service: Any = None, working_paper_service: Any = None, report_service: Any = None, ai_service: Any = None, archival_repo: Any = None, roll_forward_repo: Any = None, db_manager: Any = None) -> None:
        super().__init__()
        db = firm_service if hasattr(firm_service, "session_scope") else (db_manager if hasattr(db_manager, "session_scope") else None)
        if db:
            from finauditpro.application.services.ai_service import AIService
            self.firm_service, self.client_service = FirmService(db), ClientService(db)
            self.engagement_service, self.document_service = EngagementService(db), DocumentService(db)
            self.financial_data_service, self.audit_matrix_service = FinancialDataService(db), AuditMatrixService(db)
            self.working_paper_service, self.report_service, self.ai_service = WorkingPaperService(db), ReportService(db), AIService(db)
        else:
            self.firm_service, self.client_service = firm_service, client_service
            self.engagement_service, self.document_service = engagement_service, document_service
            self.financial_data_service, self.audit_matrix_service = financial_data_service, audit_matrix_service
            self.working_paper_service, self.report_service, self.ai_service = working_paper_service, report_service, ai_service

        self.archival_repo, self.roll_forward_repo, self.db_manager = archival_repo, roll_forward_repo, db
        self.current_firm, self.current_client, self.current_engagement = None, None, None
        self.sidebar_collapsed = False
        self.setWindowTitle("FinAuditPro — Offline-First Audit Operating System")
        self.resize(1440, 920)
        self.setStyleSheet(GLOBAL_QSS)
        self._init_ui()
        self._show_login_flow()
        self._auto_select_initial_engagement()

    @property
    def active_engagement_id(self) -> str | None:
        return self.current_engagement.id if self.current_engagement else None

    def _show_login_flow(self) -> None:
        import sys
        if "pytest" not in sys.modules:
            LoginDialog(self).exec()

    def _init_ui(self) -> None:
        central = QWidget()
        central.setObjectName("appBg")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("dashboardSidebar")
        self.sidebar.setFixedWidth(230)
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(12, 16, 12, 16)
        sb_layout.setSpacing(4)

        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(30, 30)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setObjectName("sidebarLogoBadge")
        self.logo_name = QLabel("FinAuditPro")
        self.logo_name.setObjectName("sidebarAppTitle")
        self.btn_collapse = QPushButton("◀")
        self.btn_collapse.setFixedSize(24, 24)
        self.btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_collapse.setStyleSheet("QPushButton { border: none; background: transparent; color: #64748B; font-size: 10px; font-weight: 700; } QPushButton:hover { color: #0F172A; }")
        self.btn_collapse.clicked.connect(self._toggle_sidebar)
        for w in (logo_box, self.logo_name):
            logo_row.addWidget(w)
        logo_row.addStretch()
        logo_row.addWidget(self.btn_collapse)
        sb_layout.addLayout(logo_row)
        sb_layout.addSpacing(10)

        self.btn_group = QButtonGroup(self)
        current_section = None
        for idx, (attr, title, sec) in enumerate(NAV_ITEMS):
            if sec != current_section:
                current_section = sec
                lbl = QLabel(sec)
                lbl.setObjectName("sidebarSectionLabel")
                sb_layout.addWidget(lbl)
            btn = QPushButton(title)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            setattr(self, attr, btn)
            self.btn_group.addButton(btn, idx)
            sb_layout.addWidget(btn)
        self.btn_dashboard.setChecked(True)
        sb_layout.addStretch()

        prof_frame = QFrame()
        prof_frame.setObjectName("sidebarProfileFrame")
        pf_l = QHBoxLayout(prof_frame)
        pf_l.setContentsMargins(4, 10, 4, 4)
        av = QLabel("AD")
        av.setFixedSize(28, 28)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setObjectName("userAvatar")
        u_info = QVBoxLayout()
        u_info.setSpacing(0)
        un, ur = QLabel("admin"), QLabel("Administrator")
        un.setObjectName("userName")
        ur.setObjectName("userRole")
        u_info.addWidget(un)
        u_info.addWidget(ur)
        btn_more = QPushButton("•••")
        btn_more.setFixedSize(22, 22)
        btn_more.setStyleSheet("QPushButton { border: none; background: transparent; color: #64748B; font-weight: 800; } QPushButton:hover { color: #0F172A; }")
        btn_more.clicked.connect(self._show_profile_menu)
        pf_l.addWidget(av)
        pf_l.addLayout(u_info)
        pf_l.addStretch()
        pf_l.addWidget(btn_more)
        sb_layout.addWidget(prof_frame)
        main_layout.addWidget(self.sidebar)

        # 2. Main Workspace Right Container
        right_container = QWidget()
        rc_layout = QVBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("dashboardHeader")
        header.setFixedHeight(56)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)

        search_frame = QFrame()
        search_frame.setObjectName("globalSearchFrame")
        sf_l = QHBoxLayout(search_frame)
        sf_l.setContentsMargins(10, 4, 10, 4)
        sf_s = QLineEdit()
        sf_s.setObjectName("globalSearchInput")
        sf_s.setPlaceholderText("Search clients, findings, reports...")
        sf_s.setReadOnly(True)
        sf_s.setCursor(Qt.CursorShape.PointingHandCursor)
        sf_s.mousePressEvent = lambda e: self._open_command_palette()
        sf_k = QLabel("⌘K")
        sf_k.setObjectName("globalShortcutBadge")
        sf_l.addWidget(sf_s)
        sf_l.addWidget(sf_k)
        h_layout.addWidget(search_frame)
        h_layout.addStretch()

        act_lbl = QLabel("ENGAGEMENT")
        act_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #94A3B8; letter-spacing: 0.5px;")
        self.eng_selector_combo = QComboBox()
        self.eng_selector_combo.setObjectName("clientSelectorCombo")
        self.eng_selector_combo.setMinimumWidth(260)
        self.eng_selector_combo.currentIndexChanged.connect(self._on_header_engagement_changed)

        btn_new_audit = QPushButton("+ New Audit")
        btn_new_audit.setObjectName("primaryBtn")
        btn_new_audit.clicked.connect(self._on_new_engagement)

        h_layout.addWidget(act_lbl)
        h_layout.addWidget(self.eng_selector_combo)
        h_layout.addSpacing(10)
        h_layout.addWidget(btn_new_audit)
        rc_layout.addWidget(header)

        # 3. Stacked Views
        self.stack = QStackedWidget()
        self.view_dashboard = DashboardView(self.firm_service, self.client_service, self.engagement_service)
        self.view_dashboard.navigate_to_clients.connect(lambda: self.btn_clients.click())
        self.view_dashboard.navigate_to_engagements.connect(lambda: self.btn_engagements.click())
        self.view_dashboard.navigate_to_matrix.connect(lambda: self.btn_matrix.click())
        self.view_dashboard.engagement_selected.connect(self.set_active_engagement)

        self.view_firms = FirmView(self.firm_service)
        self.view_firms.firm_selected.connect(self.set_active_firm)
        self.view_firms.firm_changed.connect(self._on_firms_changed)
        self.view_clients = ClientView(self.firm_service, self.client_service)
        self.view_clients.client_selected.connect(self.set_active_client)
        self.view_clients.client_changed.connect(self._on_clients_changed)
        self.view_engagements = EngagementView(self.firm_service, self.client_service, self.engagement_service)
        self.view_engagements.engagement_changed.connect(self.set_active_engagement)
        self.view_engagements.engagement_selected.connect(self.set_active_engagement)
        self.view_documents = DocumentView(self.document_service)
        self.view_financial_data = FinancialDataView(self.financial_data_service, self.engagement_service)
        self.view_gst, self.view_compliance = GSTVerificationView(), ComplianceView()
        self.view_audit_matrix = AuditMatrixView(self.audit_matrix_service)
        self.view_ai_assistant = AIAssistantView(self.ai_service, self.document_service, self.engagement_service)
        self.view_working_papers = WorkingPaperView(self.engagement_service, self.working_paper_service)
        self.view_reports = ReportView(self.engagement_service, self.report_service)
        self.view_archival, self.view_roll_forward, self.view_settings = ArchivalView(self.db_manager), RollForwardView(self.db_manager), SettingsView()

        for v in (self.view_dashboard, self.view_firms, self.view_clients, self.view_engagements, self.view_documents, self.view_financial_data, self.view_gst, self.view_compliance, self.view_audit_matrix, self.view_ai_assistant, self.view_working_papers, self.view_reports, self.view_archival, self.view_roll_forward, self.view_settings):
            self.stack.addWidget(v)

        rc_layout.addWidget(self.stack, stretch=1)
        main_layout.addWidget(right_container, stretch=1)
        self.btn_group.idClicked.connect(self._on_nav_clicked)

    def _toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        self.sidebar.setFixedWidth(64 if self.sidebar_collapsed else 230)
        self.logo_name.setVisible(not self.sidebar_collapsed)
        self.btn_collapse.setText("▶" if self.sidebar_collapsed else "◀")

    def _show_profile_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 4px; font-size: 12px; } QMenu::item:selected { background-color: #EFF6FF; color: #2563EB; }")
        menu.addAction("Profile && CA License", lambda: self.btn_settings.click())
        menu.addAction("System Preferences", lambda: self.btn_settings.click())
        menu.addSeparator()
        menu.addAction("Sign Out", self.close)
        menu.exec(self.cursor().pos())

    def _auto_select_initial_engagement(self) -> None:
        try:
            firms = self.firm_service.list_firms()
            if not firms:
                self._update_header_combo()
                return
            self.set_active_firm(firms[0].id)
        except Exception:
            pass

    def _on_firms_changed(self) -> None:
        self._update_header_combo()
        self.view_dashboard.refresh_dashboard()

    def _on_clients_changed(self) -> None:
        self._update_header_combo()
        self.view_dashboard.refresh_dashboard()
        self.view_engagements.refresh()

    def _on_nav_clicked(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)

    def set_active_firm(self, firm_id: str) -> None:
        firm = self.firm_service.get_firm_by_id(firm_id)
        if not firm: return
        self.current_firm = firm
        self.view_dashboard.set_firm(firm)
        self.view_clients.set_firm(firm)
        clients = self.client_service.list_clients_for_firm(firm.id)
        eng_found = next((e for c in clients for e in self.engagement_service.list_engagements_for_client(c.id)), None)
        if eng_found: self.set_active_engagement(eng_found.id)
        elif clients: self.set_active_client(clients[0].id)
        else:
            self.current_client, self.current_engagement = None, None
            self._update_header_combo()

    def set_active_client(self, client_id: str) -> None:
        client = self.client_service.get_client_by_id(client_id)
        if not client: return
        self.current_client = client
        if client.firm_id and (not self.current_firm or self.current_firm.id != client.firm_id):
            self.current_firm = self.firm_service.get_firm_by_id(client.firm_id)
            if self.current_firm:
                self.view_dashboard.set_firm(self.current_firm)
                self.view_clients.set_firm(self.current_firm)
        engs = self.engagement_service.list_engagements_for_client(client.id)
        if engs: self.set_active_engagement(engs[0].id)
        else:
            self.current_engagement = None
            for v in (self.view_documents, self.view_financial_data, self.view_gst, self.view_compliance, self.view_audit_matrix, self.view_working_papers, self.view_reports, self.view_ai_assistant, self.view_archival, self.view_roll_forward):
                getattr(v, "set_active_engagement", lambda e: None)(None)
            self._update_header_combo()

    def set_active_engagement(self, engagement_id: str) -> None:
        eng = self.engagement_service.get_engagement_by_id(engagement_id)
        if not eng: return
        self.current_engagement = eng
        self.current_client = self.client_service.get_client_by_id(eng.client_id)
        self.current_firm = self.firm_service.get_firm_by_id(self.current_client.firm_id) if self.current_client else None
        self.view_dashboard.set_firm(self.current_firm)
        for v in (self.view_documents, self.view_financial_data, self.view_gst, self.view_compliance, self.view_audit_matrix, self.view_working_papers, self.view_reports, self.view_ai_assistant, self.view_archival, self.view_roll_forward):
            getattr(v, "set_active_engagement", lambda e: None)(eng)
        self._update_header_combo()

    def _update_header_combo(self) -> None:
        self.eng_selector_combo.blockSignals(True)
        self.eng_selector_combo.clear()
        firms = self.firm_service.list_firms()
        clients = self.client_service.list_clients_for_firm(self.current_firm.id) if self.current_firm else (self.client_service.list_clients_for_firm(firms[0].id) if firms else [])
        if not clients and hasattr(self.client_service, "list_all_clients"): clients = self.client_service.list_all_clients()
        if not clients:
            self.eng_selector_combo.addItem("No Clients Registered — Select or Create Client", None)
            self.eng_selector_combo.blockSignals(False); return
        selected_idx, item_idx = 0, 0
        for c in clients:
            engs = self.engagement_service.list_engagements_for_client(c.id)
            if engs:
                for e in engs:
                    audit_t = e.audit_type.value if hasattr(e.audit_type, "value") else str(e.audit_type)
                    self.eng_selector_combo.addItem(f"{c.name} · FY {e.financial_year} · {audit_t}", f"eng:{e.id}")
                    if self.current_engagement and e.id == self.current_engagement.id: selected_idx = item_idx
                    item_idx += 1
            else:
                self.eng_selector_combo.addItem(f"{c.name} (No engagements created)", f"cli:{c.id}")
                if self.current_client and c.id == self.current_client.id and not self.current_engagement: selected_idx = item_idx
                item_idx += 1
        self.eng_selector_combo.setCurrentIndex(selected_idx)
        self.eng_selector_combo.blockSignals(False)
        if not self.current_engagement and item_idx > 0:
            first_data = self.eng_selector_combo.itemData(selected_idx)
            if first_data and str(first_data).startswith("eng:"):
                eng = self.engagement_service.get_engagement_by_id(str(first_data)[4:])
                if eng:
                    self.current_engagement = eng
                    for v in (self.view_documents, self.view_financial_data, self.view_gst, self.view_compliance, self.view_audit_matrix, self.view_working_papers, self.view_reports, self.view_ai_assistant, self.view_archival, self.view_roll_forward):
                        getattr(v, "set_active_engagement", lambda e: None)(eng)

    def _on_header_engagement_changed(self, idx: int) -> None:
        data = self.eng_selector_combo.itemData(idx)
        if data:
            self.set_active_engagement(str(data)[4:]) if str(data).startswith("eng:") else (self.set_active_client(str(data)[4:]) if str(data).startswith("cli:") else self.set_active_engagement(str(data)))

    def _on_new_engagement(self) -> None:
        firms = self.firm_service.list_firms()
        if not firms:
            QMessageBox.warning(self, "No Firm", "Please create an Audit Firm first.")
            self.btn_firms.click(); return
        firm = self.current_firm or firms[0]
        clients = self.client_service.list_clients_for_firm(firm.id)
        if not clients:
            QMessageBox.warning(self, "No Client", "Please create a Client first before adding an Engagement.")
            self.btn_clients.click(); return
        client = self.current_client or clients[0]
        dlg = EngagementDialog(self.engagement_service, firm=firm, client=client, parent=self)
        if dlg.exec() and dlg.result_engagement:
            self.set_active_engagement(dlg.result_engagement.id)
            self.view_engagements.refresh()
            self.view_dashboard.refresh_dashboard()

    def _open_command_palette(self) -> None:
        from finauditpro.ui.dialogs.command_palette_dialog import CommandPaletteDialog
        dlg = CommandPaletteDialog(self)
        dlg.action_triggered.connect(lambda k, p: self.stack.setCurrentIndex(p) if k == "nav" and 0 <= p < self.stack.count() else None)
        dlg.exec()
