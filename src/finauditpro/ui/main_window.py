"""Primary Desktop Application Shell Window for FinAuditPro."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.ai_service import AIService
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.domain.entities import Client, Engagement, Firm
from typing import Any
from finauditpro.ui.dialogs.client_dialog import ClientDialog
from finauditpro.ui.dialogs.engagement_dialog import EngagementDialog
from finauditpro.ui.dialogs.firm_dialog import FirmDialog
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


class MainWindow(QMainWindow):
    """Main Application Window."""

    def __init__(
        self,
        firm_service: Any = None,
        client_service: Any = None,
        engagement_service: Any = None,
        document_service: Any = None,
        financial_data_service: Any = None,
        audit_matrix_service: Any = None,
        working_paper_service: Any = None,
        report_service: Any = None,
        ai_service: Any = None,
        archival_repo: Any = None,
        roll_forward_repo: Any = None,
        db_manager: Any = None,
    ) -> None:
        super().__init__()
        db = firm_service if hasattr(firm_service, "session_scope") else (db_manager if hasattr(db_manager, "session_scope") else None)

        if db:
            self.firm_service = FirmService(db)
            self.client_service = ClientService(db)
            self.engagement_service = EngagementService(db)
            self.document_service = DocumentService(db)
            self.financial_data_service = FinancialDataService(db)
            self.audit_matrix_service = AuditMatrixService(db)
            self.working_paper_service = WorkingPaperService(db)
            self.report_service = ReportService(db)
            self.ai_service = AIService(db)
        else:
            self.firm_service = firm_service
            self.client_service = client_service
            self.engagement_service = engagement_service
            self.document_service = document_service
            self.financial_data_service = financial_data_service
            self.audit_matrix_service = audit_matrix_service
            self.working_paper_service = working_paper_service
            self.report_service = report_service
            self.ai_service = ai_service

        self.archival_repo = archival_repo
        self.roll_forward_repo = roll_forward_repo
        self.db_manager = db

        self.current_firm: Firm | None = None
        self.current_client: Client | None = None
        self.current_engagement: Engagement | None = None

        self.setWindowTitle("FinAuditPro — Offline-First Audit Operating System")
        self.resize(1400, 900)
        self.setStyleSheet(GLOBAL_QSS)

        self._init_ui()
        self._show_login_flow()
        self._auto_select_initial_engagement()

    @property
    def active_engagement_id(self) -> str | None:
        return self.current_engagement.id if self.current_engagement else None

    def _show_login_flow(self) -> None:
        login_dlg = LoginDialog(self)
        login_dlg.exec()

    def _init_ui(self) -> None:
        central = QWidget()
        central.setObjectName("appBg")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar Navigation
        sidebar = QFrame()
        sidebar.setObjectName("dashboardSidebar")
        sidebar.setFixedWidth(240)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 16, 12, 16)
        sb_layout.setSpacing(6)

        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(30, 30)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setObjectName("sidebarLogoBadge")
        logo_name = QLabel("FinAuditPro")
        logo_name.setObjectName("sidebarAppTitle")
        logo_row.addWidget(logo_box)
        logo_row.addWidget(logo_name)
        logo_row.addStretch()
        sb_layout.addLayout(logo_row)
        sb_layout.addSpacing(10)

        self.btn_group = QButtonGroup(self)
        btn_defs = [
            ("btn_dashboard", "  Dashboard"), ("btn_firms", "  Audit Firms"),
            ("btn_clients", "  Clients"), ("btn_engagements", "  Engagements"),
            ("btn_documents", "  Documents"), ("btn_financial_data", "  Financial Statements"),
            ("btn_gst", "  GST Reconciliation"), ("btn_compliance", "  Statutory Compliance"),
            ("btn_audit_matrix", "  Audit Matrix"), ("btn_working_papers", "  Working Papers"),
            ("btn_reports", "  Reports"), ("btn_ai_assistant", "  AI Copilot"),
            ("btn_archival", "  File Archival"), ("btn_roll_forward", "  Roll-Forward"),
            ("btn_settings", "  Settings")
        ]
        for idx, (attr, title) in enumerate(btn_defs):
            btn = QPushButton(title)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            setattr(self, attr, btn)
            self.btn_group.addButton(btn, idx)
        self.btn_dashboard.setChecked(True)

        def make_section(txt: str):
            lbl = QLabel(txt)
            lbl.setObjectName("sidebarSectionLabel")
            sb_layout.addWidget(lbl)

        make_section("WORKSPACE")
        sb_layout.addWidget(self.btn_dashboard)
        sb_layout.addWidget(self.btn_firms)
        sb_layout.addWidget(self.btn_clients)
        sb_layout.addWidget(self.btn_engagements)

        make_section("FINANCIAL")
        sb_layout.addWidget(self.btn_documents)
        sb_layout.addWidget(self.btn_financial_data)
        sb_layout.addWidget(self.btn_gst)
        sb_layout.addWidget(self.btn_compliance)

        make_section("ANALYSIS")
        sb_layout.addWidget(self.btn_audit_matrix)
        sb_layout.addWidget(self.btn_ai_assistant)

        make_section("AUDIT WORKFLOW")
        sb_layout.addWidget(self.btn_working_papers)
        sb_layout.addWidget(self.btn_reports)

        make_section("SYSTEM")
        sb_layout.addWidget(self.btn_archival)
        sb_layout.addWidget(self.btn_roll_forward)
        sb_layout.addWidget(self.btn_settings)

        sb_layout.addStretch()

        # Profile Pill Footer
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
        un = QLabel("admin")
        un.setObjectName("userName")
        ur = QLabel("Administrator")
        ur.setObjectName("userRole")
        u_info.addWidget(un)
        u_info.addWidget(ur)
        pf_l.addWidget(av)
        pf_l.addLayout(u_info)
        pf_l.addStretch()
        sb_layout.addWidget(prof_frame)

        main_layout.addWidget(sidebar)

        # 2. Main Right Container
        right_container = QWidget()
        rc_layout = QVBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.setSpacing(0)

        # Top Header Bar
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

        act_lbl = QLabel("ACTIVE AUDIT:")
        act_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #86868B;")
        self.eng_selector_combo = QComboBox()
        self.eng_selector_combo.setObjectName("clientSelectorCombo")
        self.eng_selector_combo.setMinimumWidth(240)
        self.eng_selector_combo.currentIndexChanged.connect(self._on_header_engagement_changed)

        btn_new_audit = QPushButton("+ New Audit")
        btn_new_audit.setObjectName("primaryBtn")
        btn_new_audit.clicked.connect(self._on_new_engagement)

        h_layout.addWidget(act_lbl)
        h_layout.addWidget(self.eng_selector_combo)
        h_layout.addSpacing(8)
        h_layout.addWidget(btn_new_audit)

        rc_layout.addWidget(header)

        # Stacked Views
        self.stack = QStackedWidget()
        self.view_dashboard = DashboardView(self.firm_service, self.client_service, self.engagement_service)
        self.view_dashboard.navigate_to_clients.connect(lambda: self.btn_clients.click())
        self.view_firms = FirmView(self.firm_service)
        self.view_clients = ClientView(self.firm_service, self.client_service)
        self.view_engagements = EngagementView(self.firm_service, self.client_service, self.engagement_service)
        self.view_documents = DocumentView(self.document_service)
        self.view_financial_data = FinancialDataView(self.financial_data_service, self.engagement_service)
        self.view_gst = GSTVerificationView()
        self.view_compliance = ComplianceView()
        self.view_audit_matrix = AuditMatrixView(self.audit_matrix_service)
        self.view_working_papers = WorkingPaperView(self.engagement_service, self.working_paper_service)
        self.view_reports = ReportView(self.engagement_service, self.report_service)
        self.view_ai_assistant = AIAssistantView(self.ai_service, self.document_service)
        self.view_archival = ArchivalView(self.db_manager)
        self.view_roll_forward = RollForwardView(self.db_manager)
        self.view_settings = SettingsView()

        views = [
            self.view_dashboard, self.view_firms, self.view_clients, self.view_engagements,
            self.view_documents, self.view_financial_data, self.view_gst, self.view_compliance,
            self.view_audit_matrix, self.view_ai_assistant, self.view_working_papers,
            self.view_reports, self.view_archival, self.view_roll_forward, self.view_settings
        ]
        for v in views:
            self.stack.addWidget(v)

        rc_layout.addWidget(self.stack, stretch=1)
        main_layout.addWidget(right_container, stretch=1)

        self.btn_group.idClicked.connect(self._on_nav_clicked)

        # Connect entity signals
        if hasattr(self.view_firms, "firm_selected"):
            self.view_firms.firm_selected.connect(self.set_active_firm)
        if hasattr(self.view_clients, "client_selected"):
            self.view_clients.client_selected.connect(self.set_active_client)
        if hasattr(self.view_engagements, "engagement_selected"):
            self.view_engagements.engagement_selected.connect(self.set_active_engagement)

    def _auto_select_initial_engagement(self) -> None:
        try:
            firms = self.firm_service.list_firms()
            if not firms:
                return
            firm = firms[0]
            self.current_firm = firm
            clients = self.client_service.list_clients_for_firm(firm.id)
            if not clients:
                return
            client = clients[0]
            self.current_client = client
            engs = self.engagement_service.list_engagements_for_client(client.id)
            if engs:
                self.set_active_engagement(engs[0].id)
        except Exception:
            pass

    def _on_nav_clicked(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)

    def set_active_firm(self, firm_id: str) -> None:
        firm = self.firm_service.get_firm_by_id(firm_id)
        if firm:
            self.current_firm = firm
            self.view_dashboard.set_firm(firm)

    def set_active_client(self, client_id: str) -> None:
        client = self.client_service.get_client_by_id(client_id)
        if client:
            self.current_client = client

    def set_active_engagement(self, engagement_id: str) -> None:
        eng = self.engagement_service.get_engagement_by_id(engagement_id)
        if not eng:
            return
        self.current_engagement = eng
        self.current_client = self.client_service.get_client_by_id(eng.client_id)
        self.current_firm = self.firm_service.get_firm_by_id(self.current_client.firm_id) if self.current_client else None

        self.view_dashboard.set_firm(self.current_firm)
        for v in [self.view_documents, self.view_financial_data, self.view_gst, self.view_compliance, self.view_audit_matrix, self.view_working_papers, self.view_reports, self.view_ai_assistant, self.view_archival, self.view_roll_forward]:
            getattr(v, "set_active_engagement", lambda e: None)(eng)
        self._update_header_combo()

    def _update_header_combo(self) -> None:
        self.eng_selector_combo.blockSignals(True)
        self.eng_selector_combo.clear()
        if self.current_client:
            engs = self.engagement_service.list_engagements_for_client(self.current_client.id)
            if engs:
                for idx, e in enumerate(engs):
                    audit_t = e.audit_type.value if hasattr(e.audit_type, "value") else str(e.audit_type)
                    self.eng_selector_combo.addItem(f"🏢 {self.current_client.name} — FY {e.financial_year} ({audit_t})", e.id)
                    if self.current_engagement and e.id == self.current_engagement.id:
                        self.eng_selector_combo.setCurrentIndex(idx)
            else:
                self.eng_selector_combo.addItem("No Engagements Created", None)
        else:
            self.eng_selector_combo.addItem("Select Active Audit Engagement...", None)
        self.eng_selector_combo.blockSignals(False)

    def _on_header_engagement_changed(self, idx: int) -> None:
        eng_id = self.eng_selector_combo.itemData(idx)
        if eng_id:
            self.set_active_engagement(eng_id)

    def _on_new_engagement(self) -> None:
        if not self.current_client:
            QMessageBox.warning(self, "No Client", "Please select or create a client first.")
            return
        dlg = EngagementDialog(self.current_client.id, self)
        if dlg.exec():
            eng = self.engagement_service.create_engagement(self.current_client.id, dlg.title, dlg.financial_year, dlg.audit_type)
            self.set_active_engagement(eng.id)

    def _open_command_palette(self) -> None:
        from finauditpro.ui.dialogs.command_palette_dialog import CommandPaletteDialog
        dlg = CommandPaletteDialog(self)
        dlg.action_triggered.connect(lambda k, p: self.stack.setCurrentIndex(p) if k == "nav" and 0 <= p < self.stack.count() else None)
        dlg.exec()
