"""Primary PySide6 Desktop Application Window for FinAuditPro."""

from typing import Any

from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_analytics_service import FinancialAnalyticsService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.ui.dialogs.client_dialog import ClientDialog
from finauditpro.ui.dialogs.engagement_dialog import EngagementDialog
from finauditpro.ui.dialogs.firm_dialog import FirmDialog
from finauditpro.ui.theme import apply_theme
from finauditpro.ui.views.ai_assistant_view import AIAssistantView
from finauditpro.ui.views.archival_view import ArchivalView
from finauditpro.ui.views.audit_matrix_view import AuditMatrixView
from finauditpro.ui.views.client_view import ClientView
from finauditpro.ui.views.dashboard_view import DashboardView
from finauditpro.ui.views.document_view import DocumentView
from finauditpro.ui.views.engagement_view import EngagementView
from finauditpro.ui.views.financial_data_view import FinancialDataView
from finauditpro.ui.views.firm_view import FirmView
from finauditpro.ui.dialogs.onboarding_dialog import OnboardingDialog
from finauditpro.ui.views.report_view import ReportView
from finauditpro.ui.views.roll_forward_view import RollForwardView
from finauditpro.ui.views.settings_view import SettingsView
from finauditpro.ui.views.working_paper_view import WorkingPaperView


class MainWindow(QMainWindow):
    """Main window shell for FinAuditPro application."""

    def __init__(self, db_manager: Any) -> None:
        super().__init__()
        self.db_manager = db_manager

        # Application Services
        self.firm_service = FirmService(self.db_manager)
        self.client_service = ClientService(self.db_manager)
        self.engagement_service = EngagementService(self.db_manager)
        self.document_service = DocumentService(self.db_manager)
        self.financial_data_service = FinancialDataService(self.db_manager)
        self.financial_analytics_service = FinancialAnalyticsService(self.db_manager)
        self.materiality_service = MaterialityService(self.db_manager)
        self.audit_matrix_service = AuditMatrixService(self.db_manager)
        self.working_paper_service = WorkingPaperService(self.db_manager)
        self.report_service = ReportService(self.db_manager)
        from finauditpro.application.services.ai_service_factory import create_ai_service

        self.ai_service = create_ai_service(self.db_manager)

        self.active_engagement_id: str | None = None

        self.setWindowTitle("FinAuditPro — Offline-First Audit Operating System")
        self.resize(1280, 800)

        self._init_ui()
        self._load_initial_state()

    def _init_ui(self) -> None:
        apply_theme(self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Header Bar with Context Info
        header_bar = QWidget()
        header_bar.setObjectName("HeaderContextBar")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(20, 10, 20, 10)

        logo_label = QLabel("FINAUDITPRO")
        logo_label.setObjectName("HeaderTitle")

        sub_label = QLabel("PRIVACY-FIRST AUDIT INTELLIGENCE PLATFORM")
        sub_label.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #64748b; margin-left: 8px;"
        )

        self.header_context_lbl = QLabel("No active engagement")
        self.header_context_lbl.setObjectName("HeaderContextLabel")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(sub_label)
        header_layout.addStretch()
        header_layout.addWidget(self.header_context_lbl)

        root_layout.addWidget(header_bar)

        # 2. Main Content Splitter (Sidebar + Stacked Views)
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar navigation
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(8)

        self.btn_group = QButtonGroup(self)
        btn_defs = [
            ("btn_dashboard", "  Dashboard"), ("btn_firms", "  Audit Firms"),
            ("btn_clients", "  Clients"), ("btn_engagements", "  Engagements"),
            ("btn_documents", "  Documents"), ("btn_financial_data", "  Financial Data"),
            ("btn_audit_matrix", "  Audit Matrix"), ("btn_working_papers", "  Working Papers"),
            ("btn_reports", "  Reports"), ("btn_ai_assistant", "  AI Copilot"),
            ("btn_archival", "  File Archival"), ("btn_roll_forward", "  Roll-Forward"),
            ("btn_settings", "  Settings")
        ]
        for idx, (attr, title) in enumerate(btn_defs):
            btn = QPushButton(title)
            btn.setCheckable(True)
            setattr(self, attr, btn)
            self.btn_group.addButton(btn, idx)
        self.btn_dashboard.setChecked(True)

        def make_section(txt: str):
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; margin-left: 6px; margin-top: 6px; margin-bottom: 2px;")
            sb_layout.addWidget(lbl)

        make_section("AUDIT WORKSPACE")
        sb_layout.addWidget(self.btn_dashboard)
        sb_layout.addWidget(self.btn_firms)
        sb_layout.addWidget(self.btn_clients)
        sb_layout.addWidget(self.btn_engagements)

        make_section("EVIDENCE & ANALYTICS")
        sb_layout.addWidget(self.btn_documents)
        sb_layout.addWidget(self.btn_financial_data)
        sb_layout.addWidget(self.btn_audit_matrix)

        make_section("WORK & REVIEWS")
        sb_layout.addWidget(self.btn_working_papers)
        sb_layout.addWidget(self.btn_reports)
        sb_layout.addWidget(self.btn_ai_assistant)

        make_section("OUTPUT & SYSTEM")
        sb_layout.addWidget(self.btn_archival)
        sb_layout.addWidget(self.btn_roll_forward)
        sb_layout.addWidget(self.btn_settings)

        # Action shortcuts
        sb_layout.addSpacing(20)
        action_title = QLabel("QUICK ACTIONS")
        action_title.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #64748b; margin-left: 8px; margin-bottom: 4px;"
        )
        sb_layout.addWidget(action_title)

        btn_new_firm = QPushButton("+ New Firm")
        btn_new_firm.setObjectName("SecondaryButton")
        btn_new_firm.clicked.connect(self._quick_new_firm)

        btn_new_client = QPushButton("+ New Client")
        btn_new_client.setObjectName("SecondaryButton")
        btn_new_client.clicked.connect(self._quick_new_client)

        btn_new_eng = QPushButton("+ New Engagement")
        btn_new_eng.setObjectName("SecondaryButton")
        btn_new_eng.clicked.connect(self._quick_new_engagement)

        sb_layout.addWidget(btn_new_firm)
        sb_layout.addWidget(btn_new_client)
        sb_layout.addWidget(btn_new_eng)

        sb_layout.addStretch()

        body_layout.addWidget(sidebar)

        # Views Stack — insertion order MUST match button group IDs above
        self.stack = QStackedWidget()

        self.dashboard_view = DashboardView(
            self.firm_service, self.client_service, self.engagement_service
        )
        self.dashboard_view.engagement_selected.connect(self._on_engagement_selected)

        self.firm_view = FirmView(self.firm_service)
        self.firm_view.firm_changed.connect(self._on_state_changed)

        self.client_view = ClientView(self.firm_service, self.client_service)
        self.client_view.client_changed.connect(self._on_state_changed)

        self.engagement_view = EngagementView(
            self.firm_service, self.client_service, self.engagement_service
        )
        self.engagement_view.engagement_changed.connect(self._on_engagement_selected)

        self.document_view = DocumentView(self.document_service)
        self.document_view.document_changed.connect(self._on_state_changed)

        self.financial_data_view = FinancialDataView(
            self.client_service,
            self.engagement_service,
            self.financial_data_service,
            self.financial_analytics_service,
        )
        self.financial_data_view.data_changed.connect(self._on_state_changed)

        self.audit_matrix_view = AuditMatrixView(
            self.engagement_service,
            self.materiality_service,
            self.audit_matrix_service,
        )
        self.audit_matrix_view.matrix_changed.connect(self._on_state_changed)

        self.working_paper_view = WorkingPaperView(
            self.engagement_service,
            self.working_paper_service,
        )
        self.working_paper_view.wp_changed.connect(self._on_state_changed)

        self.report_view = ReportView(
            self.engagement_service,
            self.report_service,
        )
        self.report_view.report_changed.connect(self._on_state_changed)

        self.ai_assistant_view = AIAssistantView(
            self.engagement_service,
            self.ai_service,
        )
        self.ai_assistant_view.ai_changed.connect(self._on_state_changed)

        self.archival_view = ArchivalView(self.db_manager)
        self.roll_forward_view = RollForwardView(self.db_manager)
        self.settings_view = SettingsView()

        self.stack.addWidget(self.dashboard_view)  # 0
        self.stack.addWidget(self.firm_view)  # 1
        self.stack.addWidget(self.client_view)  # 2
        self.stack.addWidget(self.engagement_view)  # 3
        self.stack.addWidget(self.document_view)  # 4
        self.stack.addWidget(self.financial_data_view)  # 5
        self.stack.addWidget(self.audit_matrix_view)  # 6
        self.stack.addWidget(self.working_paper_view)  # 7
        self.stack.addWidget(self.report_view)  # 8
        self.stack.addWidget(self.ai_assistant_view)  # 9
        self.stack.addWidget(self.archival_view)  # 10
        self.stack.addWidget(self.roll_forward_view)  # 11
        self.stack.addWidget(self.settings_view)  # 12

        self.btn_group.idClicked.connect(self.stack.setCurrentIndex)

        body_layout.addWidget(self.stack, stretch=1)
        root_layout.addWidget(body_widget, stretch=1)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(
            "background-color: #121418; color: #64748b; border-top: 1px solid #2e3440;"
        )
        self.status_bar.showMessage(
            "SQLite Engine Active (WAL Mode) | Offline-First Security Guaranteed"
        )
        self.setStatusBar(self.status_bar)

    def _load_initial_state(self) -> None:
        """Load initial state from database into views."""
        firms = self.firm_service.list_firms()
        if firms:
            self.client_view.set_firm(firms[0])

        engagements = self.engagement_service.list_all_engagements()
        if engagements and not self.active_engagement_id:
            self._on_engagement_selected(engagements[0].id)
        else:
            self._on_state_changed()

    def _on_state_changed(self) -> None:
        """Refresh active context and all subviews."""
        firms = self.firm_service.list_firms()
        if firms and not self.client_view.current_firm:
            self.client_view.set_firm(firms[0])

        self.firm_view.refresh()
        self.client_view.refresh()
        self.engagement_view.refresh()
        self.document_view.set_engagement(self.active_engagement_id)
        self.financial_data_view.set_engagement(self.active_engagement_id)
        self.audit_matrix_view.set_engagement(self.active_engagement_id)
        self.ai_assistant_view.set_engagement(self.active_engagement_id)
        self.dashboard_view.refresh(self.active_engagement_id)

        self._update_header_context()

    def _on_engagement_selected(self, engagement_id: str) -> None:
        self.active_engagement_id = engagement_id
        for fn in [
            lambda: self.document_view.set_engagement(engagement_id),
            lambda: self.financial_data_view.set_engagement(engagement_id),
            lambda: self.audit_matrix_view.set_engagement(engagement_id),
            lambda: self.ai_assistant_view.set_engagement(engagement_id),
            lambda: self.archival_view.load_engagement(engagement_id),
            lambda: self.roll_forward_view.load_engagement(engagement_id),
            lambda: self.dashboard_view.refresh(engagement_id),
        ]:
            try:
                fn()
            except Exception:
                pass
        self._update_header_context()

    def _update_header_context(self) -> None:
        if self.active_engagement_id:
            try:
                eng = self.engagement_service.get_engagement(self.active_engagement_id)
                client = self.client_service.get_client(eng.client_id)
                firm = self.firm_service.get_firm(eng.firm_id)
                self.header_context_lbl.setText(f"Active: {firm.name} ➔ {client.name} ➔ {eng.audit_type.value} ({eng.financial_year})")
                return
            except Exception:
                pass
        self.header_context_lbl.setText("No Active Engagement Selected")

    def _quick_new_firm(self) -> None:
        dialog = FirmDialog(self.firm_service, parent=self)
        if dialog.exec() == FirmDialog.DialogCode.Accepted:
            self._on_state_changed()

    def _quick_new_client(self) -> None:
        firms = self.firm_service.list_firms()
        if not firms:
            QMessageBox.warning(self, "No Audit Firm", "Please create an Audit Firm first.")
            return
        dialog = ClientDialog(self.client_service, firm=firms[0], parent=self)
        if dialog.exec() == ClientDialog.DialogCode.Accepted:
            self._on_state_changed()

    def _quick_new_engagement(self) -> None:
        firms = self.firm_service.list_firms()
        if not firms:
            QMessageBox.warning(self, "No Audit Firm", "Please create an Audit Firm first.")
            return
        firm = firms[0]
        clients = self.client_service.list_clients_for_firm(firm.id)
        if not clients:
            QMessageBox.warning(self, "No Client", "Please create a Client first.")
            return
        dialog = EngagementDialog(
            self.engagement_service, firm=firm, client=clients[0], parent=self
        )
        if dialog.exec() == EngagementDialog.DialogCode.Accepted:
            if dialog.result_engagement:
                self.active_engagement_id = dialog.result_engagement.id
            self._on_state_changed()
