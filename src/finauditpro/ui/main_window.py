"""Main Application Shell Window for FinAuditPro Enterprise Audit Operating System."""

from typing import Any

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.audit_query_service import AuditQueryService
from finauditpro.application.services.auth_service import AuthService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_request_service import DocumentRequestService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.domain.entities import RoleEnum
from finauditpro.ui.components.context_bar import WorkspaceContextBar
from finauditpro.ui.components.header import GlobalHeaderBar
from finauditpro.ui.components.sidebar import PRIMARY_NAV_ITEMS, NavigationSidebar
from finauditpro.ui.dialogs.engagement_dialog import EngagementDialog
from finauditpro.ui.dialogs.login_dialog import LoginDialog
from finauditpro.ui.dialogs.onboarding_dialog import OnboardingDialog
from finauditpro.ui.styles import GLOBAL_QSS

# Legacy Navigation Definitions preserved for backward compatibility
NAV_ITEMS = [
    ("btn_dashboard", "Command Center", "WORKSPACE"),
    ("btn_pbc", "Intake && PBC", "GUIDED PIPELINE"),
    ("btn_audit_matrix", "Planning && SA 320", "GUIDED PIPELINE"),
    ("btn_financial_data", "TB/GL && Scrutiny", "GUIDED PIPELINE"),
    ("btn_working_papers", "Working Papers", "GUIDED PIPELINE"),
    ("btn_reports", "Reports && Sign-Off", "GUIDED PIPELINE"),
    ("btn_queries", "Client Queries", "FIELDWORK TOOLS"),
    ("btn_documents", "Uploaded Evidence", "FIELDWORK TOOLS"),
    ("btn_gst", "GST 2B Reconciler", "FIELDWORK TOOLS"),
    ("btn_compliance", "Compliance Checklist", "FIELDWORK TOOLS"),
    ("btn_inspection", "PRB Inspection Sandbox", "FIELDWORK TOOLS"),
    ("btn_ai_assistant", "AI Copilot Lab", "FIELDWORK TOOLS"),
    ("btn_clients", "Clients", "ADMINISTRATION"),
    ("btn_engagements", "Engagements", "ADMINISTRATION"),
    ("btn_firms", "Audit Firms", "ADMINISTRATION"),
    ("btn_archival", "Archival && Sealing", "SYSTEM"),
    ("btn_roll_forward", "Roll-Forward Tie-Out", "SYSTEM"),
    ("btn_settings", "Settings", "SYSTEM"),
]

GUIDED_STEPS = [
    ("Intake && PBC", "btn_pbc"),
    ("Planning (SA 320)", "btn_audit_matrix"),
    ("TB/GL Scrutiny", "btn_financial_data"),
    ("Workpapers", "btn_working_papers"),
    ("Report && Sign-Off", "btn_reports"),
]

# Category sub-navigation configurations
CATEGORY_SUB_TABS: dict[int, list[tuple[str, str]]] = {
    0: [("dashboard", "Overview")],
    1: [("inbox", "Unified Practice Inbox"), ("pbc", "Intake & PBC Requests"), ("queries", "Client Queries")],
    2: [
        ("clients", "Client Directory"),
        ("client_workspace", "Client Workspace"),
        ("engagements", "Engagements"),
        ("firms", "Audit Firms"),
    ],
    3: [
        ("work_center", "Work Center"),
        ("compliance", "Compliance Checklist"),
        ("inspection", "PRB Inspection Sandbox"),
        ("gst", "GST 2B Reconciler"),
    ],
    4: [
        ("guided_workflow", "Guided Audit Workflow"),
        ("audit_matrix", "Planning & SA 320"),
        ("financial_data", "TB/GL Scrutiny"),
        ("working_papers", "Working Papers"),
        ("documents", "Evidence Store"),
        ("reports", "Reports & Sign-Off"),
    ],
    5: [("ai_assistant", "Copilot Lab")],
    6: [
        ("settings", "Settings & Backup"),
        ("archival", "Archival & Sealing"),
        ("roll_forward", "Roll-Forward Tie-Out"),
    ],
}


def _tag(w: Any, name: str) -> Any:
    w.setObjectName(name)
    return w


class MainWindow(QMainWindow):
    """Main Application Shell Window for FinAuditPro Enterprise Audit Operating System."""

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
        db = (
            firm_service
            if hasattr(firm_service, "session_scope")
            else (db_manager if hasattr(db_manager, "session_scope") else None)
        )

        if db:
            from finauditpro.application.services.ai_service import AIService

            (
                self.firm_service,
                self.client_service,
                self.engagement_service,
                self.document_service,
            ) = FirmService(db), ClientService(db), EngagementService(db), DocumentService(db)
            self.financial_data_service, self.audit_matrix_service, self.working_paper_service = (
                FinancialDataService(db),
                AuditMatrixService(db),
                WorkingPaperService(db),
            )
            (
                self.report_service,
                self.ai_service,
                self.pbc_service,
                self.query_service,
                self.auth_service,
            ) = (
                ReportService(db),
                AIService(db),
                DocumentRequestService(db),
                AuditQueryService(db),
                AuthService(db),
            )
        else:
            (
                self.firm_service,
                self.client_service,
                self.engagement_service,
                self.document_service,
            ) = firm_service, client_service, engagement_service, document_service
            (
                self.financial_data_service,
                self.audit_matrix_service,
                self.working_paper_service,
                self.report_service,
                self.ai_service,
            ) = (
                financial_data_service,
                audit_matrix_service,
                working_paper_service,
                report_service,
                ai_service,
            )
            self.pbc_service, self.query_service, self.auth_service = (
                DocumentRequestService(firm_service.db_manager if firm_service else None),
                AuditQueryService(firm_service.db_manager if firm_service else None),
                AuthService(firm_service.db_manager if firm_service else None),
            )

        self.archival_repo, self.roll_forward_repo, self.db_manager = (
            archival_repo,
            roll_forward_repo,
            db,
        )
        self.current_firm, self.current_client, self.current_engagement = None, None, None
        self.current_user_session = UserSession(
            user_id="default", username="admin@finauditpro.com", role=RoleEnum.ADMINISTRATOR
        )
        self.sidebar_collapsed = False
        self.current_category_idx = 0

        # Legacy button mapping dictionary for backward compatibility
        self.legacy_buttons: dict[str, QPushButton] = {}
        self.route_to_widget_map: dict[str, QWidget] = {}
        self.route_to_index_map: dict[str, int] = {}

        self.setWindowTitle("FinAuditPro — Guided Statutory Audit Operating System")
        self.resize(1440, 920)
        self.setStyleSheet(GLOBAL_QSS)

        self._init_legacy_button_handles()
        self._init_ui()
        self._show_login_flow()
        self._setup_inactivity_timer()
        self._auto_select_initial_engagement()

    @property
    def active_engagement_id(self) -> str | None:
        return self.current_engagement.id if self.current_engagement else None

    def _init_legacy_button_handles(self) -> None:
        """Creates dummy or proxy button instances for legacy self.btn_* attributes."""

        def create_btn(key: str) -> QPushButton:
            btn = QPushButton()
            btn.setObjectName(key)
            self.legacy_buttons[key] = btn
            setattr(self, key, btn)
            return btn

        for attr, _, _ in NAV_ITEMS:
            create_btn(attr)

        # Primary Hub buttons
        for hub_key in ["btn_inbox", "btn_clients_hub", "btn_work", "btn_audit", "btn_system"]:
            if not hasattr(self, hub_key):
                create_btn(hub_key)

    def _show_login_flow(self) -> None:
        import sys

        if "pytest" not in sys.modules and self.auth_service:
            if self.auth_service.is_first_run():
                dlg = OnboardingDialog(self, auth_service=self.auth_service)
            else:
                dlg = LoginDialog(self, auth_service=self.auth_service)
            if dlg.exec() and dlg.authenticated_session:
                self.current_user_session = dlg.authenticated_session
                self._apply_user_session()
            else:
                sys.exit(0)

    def _apply_user_session(self) -> None:
        if self.current_user_session:
            name = self.current_user_session.username.split("@")[0].title()
            role_str = (
                self.current_user_session.role.value
                if hasattr(self.current_user_session.role, "value")
                else str(self.current_user_session.role)
            )
            self.sidebar.set_user_info(name, role_str)
            if hasattr(self, "lbl_user_name"):
                self.lbl_user_name.setText(name)
            if hasattr(self, "lbl_user_role"):
                self.lbl_user_role.setText(role_str)
            if hasattr(self, "view_working_papers") and self.view_working_papers:
                self.view_working_papers.set_user_session(self.current_user_session)

    def _init_ui(self) -> None:
        central = _tag(QWidget(), "appBg")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Reusable Primary Navigation Sidebar
        self.sidebar = NavigationSidebar(self)
        self.sidebar.category_changed.connect(self._on_category_changed)
        self.sidebar.profile_menu_requested.connect(self._show_profile_menu)
        main_layout.addWidget(self.sidebar)

        # Right Container
        right_container = QWidget()
        rc_layout = QVBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.setSpacing(0)

        # Reusable Persistent Global Header Bar
        self.header = GlobalHeaderBar(self)
        self.header.search_clicked.connect(self._open_command_palette)
        self.header.new_engagement_clicked.connect(self._on_new_engagement)
        self.header.copilot_toggled.connect(self._toggle_ai_drawer)
        self.header.engagement_changed.connect(self._on_header_engagement_changed)
        self.header.empty_engagement_clicked.connect(self._handle_empty_engagement_click)

        # Proxy handles for header widgets for legacy tests/access
        self.eng_selector_combo = self.header.eng_selector_combo
        self.btn_copilot_toggle = self.header.btn_copilot_toggle
        self.lbl_user_name = self.sidebar.lbl_user_name
        self.lbl_user_role = self.sidebar.lbl_user_role
        self.btn_collapse = self.sidebar.btn_collapse

        rc_layout.addWidget(self.header)

        # Reusable Workspace Context Bar (Sub-tabs & Breadcrumbs)
        self.context_bar = WorkspaceContextBar(self)
        self.context_bar.sub_tab_selected.connect(self._on_sub_tab_selected)
        rc_layout.addWidget(self.context_bar)

        # Main Body Stack + AI Drawer
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self._init_views()
        body_layout.addWidget(self.stack, stretch=1)

        from finauditpro.ui.views.ai_copilot_drawer import AICopilotDrawer

        self.ai_drawer = AICopilotDrawer(self.ai_service, parent=self)
        self.ai_drawer.setVisible(False)
        self.ai_drawer.closed.connect(lambda: self.ai_drawer.setVisible(False))
        body_layout.addWidget(self.ai_drawer)

        rc_layout.addLayout(body_layout, stretch=1)
        main_layout.addWidget(right_container, stretch=1)

        self._connect_legacy_buttons()
        self._register_shortcuts()
        self._on_category_changed(0)  # Start at Command Center

    def _connect_legacy_buttons(self) -> None:
        """Connects legacy button click signals to route handlers."""
        route_map: dict[str, str] = {
            "btn_dashboard": "dashboard",
            "btn_pbc": "pbc",
            "btn_audit_matrix": "audit_matrix",
            "btn_financial_data": "financial_data",
            "btn_working_papers": "working_papers",
            "btn_reports": "reports",
            "btn_queries": "queries",
            "btn_documents": "documents",
            "btn_gst": "gst",
            "btn_compliance": "compliance",
            "btn_inspection": "inspection",
            "btn_ai_assistant": "ai_assistant",
            "btn_clients": "clients",
            "btn_engagements": "engagements",
            "btn_firms": "firms",
            "btn_archival": "archival",
            "btn_roll_forward": "roll_forward",
            "btn_settings": "settings",
        }

        for attr, route_key in route_map.items():
            btn = getattr(self, attr, None)
            if btn:
                btn.clicked.connect(lambda _, r=route_key: self.navigate_to_route(r))

    def _register_shortcuts(self) -> None:
        for s, h in [
            (("Ctrl+K", "Meta+K"), self._toggle_ai_drawer),
            (("Ctrl+P", "Meta+P"), self._open_command_palette),
            (("Ctrl+Q", "Meta+Q", "Alt+F4"), self.close),
            (("Ctrl+W", "Meta+W"), self._handle_close_shortcut),
            (("Ctrl+R", "Meta+R", "F5"), self._handle_refresh_shortcut),
            (("Ctrl+,", "Meta+,"), lambda: self.navigate_to_route("settings")),
            (("Ctrl+N", "Meta+N"), self._on_new_engagement),
            (("Ctrl+L", "Meta+L"), self._lock_workstation),
        ]:
            for seq in s:
                QShortcut(QKeySequence(seq), self, h)

    def _handle_close_shortcut(self) -> None:
        self.ai_drawer.setVisible(False) if self.ai_drawer.isVisible() else self.close()

    def _handle_refresh_shortcut(self) -> None:
        self.view_dashboard.refresh_dashboard()
        curr_view = self.stack.currentWidget()
        if hasattr(curr_view, "refresh"):
            curr_view.refresh()

    def _handle_empty_engagement_click(self) -> None:
        self.navigate_to_route("clients")
        if hasattr(self.view_clients, "_create_client"):
            self.view_clients._create_client()

    def _init_views(self) -> None:
        from finauditpro.application.services.practice_dashboard_service import (
            PracticeDashboardService,
        )
        from finauditpro.ui.views.ai_assistant_view import AIAssistantView
        from finauditpro.ui.views.archival_view import ArchivalView
        from finauditpro.ui.views.audit_matrix_view import AuditMatrixView
        from finauditpro.ui.views.audit_query_view import AuditQueryView
        from finauditpro.ui.views.client_view import ClientView
        from finauditpro.ui.views.compliance_view import ComplianceView
        from finauditpro.ui.views.dashboard_view import DashboardView
        from finauditpro.ui.views.document_view import DocumentView
        from finauditpro.ui.views.engagement_view import EngagementView
        from finauditpro.ui.views.financial_data_view import FinancialDataView
        from finauditpro.ui.views.firm_view import FirmView
        from finauditpro.ui.views.gst_verification_view import GSTVerificationView
        from finauditpro.ui.views.inspection_view import InspectionView
        from finauditpro.ui.views.pbc_tracker_view import PBCTrackerView
        from finauditpro.ui.views.report_view import ReportView
        from finauditpro.ui.views.roll_forward_view import RollForwardView
        from finauditpro.ui.views.settings_view import SettingsView
        from finauditpro.ui.views.working_paper_view import WorkingPaperView

        self.practice_dashboard_service = (
            PracticeDashboardService(self.db_manager) if hasattr(self, "db_manager") and self.db_manager else None
        )

        self.view_dashboard = DashboardView(
            self.firm_service,
            self.client_service,
            self.engagement_service,
            self.audit_matrix_service,
            practice_dashboard_service=self.practice_dashboard_service,
        )
        self.view_dashboard.navigate_to_clients.connect(lambda: self.navigate_to_route("clients"))
        self.view_dashboard.navigate_to_engagements.connect(
            lambda: self.navigate_to_route("engagements")
        )
        self.view_dashboard.navigate_to_matrix.connect(
            lambda: self.navigate_to_route("audit_matrix")
        )
        self.view_dashboard.navigate_to_pbc.connect(lambda: self.navigate_to_route("pbc"))
        self.view_dashboard.navigate_to_documents.connect(lambda: self.navigate_to_route("documents"))
        self.view_dashboard.navigate_to_working_papers.connect(
            lambda: self.navigate_to_route("working_papers")
        )
        self.view_dashboard.navigate_to_reports.connect(lambda: self.navigate_to_route("reports"))
        self.view_dashboard.navigate_to_route.connect(self.navigate_to_route)
        self.view_dashboard.engagement_selected.connect(self.set_active_engagement)

        self.view_firms, self.view_clients = (
            FirmView(self.firm_service),
            ClientView(self.firm_service, self.client_service),
        )
        self.view_firms.firm_selected.connect(self.set_active_firm)
        self.view_firms.firm_changed.connect(self._on_firms_changed)
        self.view_clients.client_selected.connect(self.set_active_client)
        self.view_clients.client_changed.connect(self._on_clients_changed)

        self.view_engagements = EngagementView(
            self.firm_service, self.client_service, self.engagement_service
        )
        self.view_engagements.engagement_changed.connect(self.set_active_engagement)
        self.view_engagements.engagement_selected.connect(self.set_active_engagement)

        self.view_documents, self.view_financial_data = (
            DocumentView(self.document_service),
            FinancialDataView(self.financial_data_service, self.engagement_service),
        )
        self.view_gst, self.view_compliance, self.view_audit_matrix = (
            GSTVerificationView(),
            ComplianceView(),
            AuditMatrixView(self.audit_matrix_service),
        )
        self.view_inspection = InspectionView(
            self.engagement_service, self.working_paper_service, self.audit_matrix_service
        )
        self.view_ai_assistant = AIAssistantView(
            self.ai_service, self.document_service, self.engagement_service
        )
        self.view_working_papers, self.view_reports = (
            WorkingPaperView(
                self.engagement_service,
                self.working_paper_service,
                document_service=self.document_service,
            ),
            ReportView(self.engagement_service, self.report_service),
        )
        from finauditpro.application.services.inbox_service import InboxService
        from finauditpro.ui.views.inbox_view import InboxView

        self.inbox_service = (
            InboxService(self.db_manager) if hasattr(self, "db_manager") and self.db_manager else None
        )
        self.view_inbox = InboxView(self.inbox_service) if self.inbox_service else None
        if self.view_inbox:
            self.view_inbox.navigate_to_route.connect(self.navigate_to_route)

        self.view_pbc, self.view_queries = (
            PBCTrackerView(self.pbc_service),
            AuditQueryView(self.query_service),
        )
        self.view_archival, self.view_roll_forward, self.view_settings = (
            ArchivalView(self.db_manager),
            RollForwardView(self.db_manager),
            SettingsView(auth_service=self.auth_service),
        )

        from finauditpro.application.services.client_workspace_service import ClientWorkspaceService
        from finauditpro.application.services.work_center_service import WorkCenterService
        from finauditpro.ui.views.client_workspace_view import ClientWorkspaceView
        from finauditpro.ui.views.work_center_view import WorkCenterView

        self.client_workspace_service = (
            ClientWorkspaceService(self.db_manager) if hasattr(self, "db_manager") and self.db_manager else None
        )
        self.view_client_workspace = ClientWorkspaceView(self.client_workspace_service) if self.client_workspace_service else None
        if self.view_client_workspace:
            self.view_client_workspace.engagement_selected.connect(self.set_active_engagement)
            self.view_client_workspace.navigate_to_route.connect(self.navigate_to_route)

        self.work_center_service = (
            WorkCenterService(self.db_manager) if hasattr(self, "db_manager") and self.db_manager else None
        )
        self.view_work_center = WorkCenterView(self.work_center_service) if self.work_center_service else None

        from finauditpro.ui.views.guided_workflow_view import GuidedWorkflowView
        from finauditpro.ui.views.unified_reconciliation_view import UnifiedReconciliationView

        self.view_guided_workflow = (
            GuidedWorkflowView(self.db_manager) if hasattr(self, "db_manager") and self.db_manager else None
        )
        if self.view_guided_workflow:
            self.view_guided_workflow.navigate_to_route.connect(self.navigate_to_route)

        self.view_reconciliations = (
            UnifiedReconciliationView(self.db_manager, ai_service=self.ai_service)
            if hasattr(self, "db_manager") and self.db_manager else None
        )

        routes_with_widgets: list[tuple[str, QWidget]] = [
            ("dashboard", self.view_dashboard),
            ("inbox", self.view_inbox if self.view_inbox else self.view_pbc),
            ("work_center", self.view_work_center if self.view_work_center else self.view_pbc),
            ("guided_workflow", self.view_guided_workflow if self.view_guided_workflow else self.view_audit_matrix),
            ("reconciliations", self.view_reconciliations if self.view_reconciliations else self.view_gst),
            ("pbc", self.view_pbc),
            ("audit_matrix", self.view_audit_matrix),
            ("financial_data", self.view_financial_data),
            ("working_papers", self.view_working_papers),
            ("reports", self.view_reports),
            ("queries", self.view_queries),
            ("documents", self.view_documents),
            ("gst", self.view_gst),
            ("compliance", self.view_compliance),
            ("inspection", self.view_inspection),
            ("ai_assistant", self.view_ai_assistant),
            ("clients", self.view_clients),
            ("client_workspace", self.view_client_workspace if self.view_client_workspace else self.view_clients),
            ("engagements", self.view_engagements),
            ("firms", self.view_firms),
            ("archival", self.view_archival),
            ("roll_forward", self.view_roll_forward),
            ("settings", self.view_settings),
        ]

        for route_key, widget in routes_with_widgets:
            idx = self.stack.addWidget(widget)
            self.route_to_widget_map[route_key] = widget
            self.route_to_index_map[route_key] = idx

    def _on_category_changed(self, cat_idx: int) -> None:
        """Handles primary sidebar category changes."""
        self.current_category_idx = cat_idx
        sub_tabs = CATEGORY_SUB_TABS.get(cat_idx, [])
        cat_title = PRIMARY_NAV_ITEMS[cat_idx][1] if 0 <= cat_idx < len(PRIMARY_NAV_ITEMS) else ""

        self.sidebar.set_active_category_by_index(cat_idx)

        if sub_tabs:
            first_route = sub_tabs[0][0]
            self.context_bar.set_sub_tabs(sub_tabs, active_key=first_route)
            self.context_bar.set_breadcrumb(f"{cat_title} / {sub_tabs[0][1]}")
            self.navigate_to_route(first_route, update_context_bar=False)
        else:
            self.context_bar.set_sub_tabs([])
            self.context_bar.set_breadcrumb(cat_title)

    def _on_sub_tab_selected(self, route_key: str) -> None:
        """Handles sub-tab selection within the current category."""
        sub_tabs = CATEGORY_SUB_TABS.get(self.current_category_idx, [])
        sub_title = next((title for k, title in sub_tabs if k == route_key), "")
        cat_title = (
            PRIMARY_NAV_ITEMS[self.current_category_idx][1]
            if 0 <= self.current_category_idx < len(PRIMARY_NAV_ITEMS)
            else ""
        )
        self.context_bar.set_breadcrumb(f"{cat_title} / {sub_title}")
        self.navigate_to_route(route_key, update_context_bar=False)

    def navigate_to_route(self, route_key: str, update_context_bar: bool = True) -> None:
        """Navigates to a specific view by route key and updates active category/tab state."""
        if route_key not in self.route_to_index_map:
            return

        idx = self.route_to_index_map[route_key]
        self.stack.setCurrentIndex(idx)

        # Determine category for this route: preserve current category if route is within it
        curr_sub_tabs = CATEGORY_SUB_TABS.get(self.current_category_idx, [])
        if any(k == route_key for k, _ in curr_sub_tabs):
            found_cat_idx = self.current_category_idx
        else:
            found_cat_idx = None
            for cat_i, sub_tabs in CATEGORY_SUB_TABS.items():
                if any(k == route_key for k, _ in sub_tabs):
                    found_cat_idx = cat_i
                    break

        if found_cat_idx is not None:
            self.current_category_idx = found_cat_idx
            self.sidebar.set_active_category_by_index(found_cat_idx)
            if update_context_bar:
                sub_tabs = CATEGORY_SUB_TABS.get(found_cat_idx, [])
                self.context_bar.set_sub_tabs(sub_tabs, active_key=route_key)
                sub_title = next((t for k, t in sub_tabs if k == route_key), "")
                cat_title = PRIMARY_NAV_ITEMS[found_cat_idx][1]
                self.context_bar.set_breadcrumb(f"{cat_title} / {sub_title}")

    def _toggle_ai_drawer(self) -> None:
        if not self.ai_drawer.isVisible():
            curr_widget = self.stack.currentWidget()
            view_name = "Command Center"
            for k, w in self.route_to_widget_map.items():
                if w == curr_widget:
                    view_name = k.replace("_", " ").title()
                    break

            c_id = self.current_client.id if hasattr(self, "current_client") and self.current_client else None
            c_name = self.current_client.name if hasattr(self, "current_client") and self.current_client else None
            f_id = self.current_firm.id if hasattr(self, "current_firm") and self.current_firm else None
            f_name = self.current_firm.name if hasattr(self, "current_firm") and self.current_firm else None
            e_id = self.current_engagement.id if hasattr(self, "current_engagement") and self.current_engagement else None
            e_name = self.current_engagement.audit_type if hasattr(self, "current_engagement") and self.current_engagement else None
            fy = self.current_engagement.financial_year if hasattr(self, "current_engagement") and self.current_engagement else "FY 2025-26"

            from finauditpro.application.dtos_copilot import CopilotContextDTO
            ctx = CopilotContextDTO(
                firm=f_name,
                firm_id=f_id,
                client=c_name,
                client_id=c_id,
                financial_year=fy,
                engagement=e_name,
                engagement_id=e_id,
                current_view=view_name,
            )
            self.ai_drawer.set_context(ctx)

        self.ai_drawer.setVisible(not self.ai_drawer.isVisible())
        if self.ai_drawer.isVisible():
            self.ai_drawer.inp_query.setFocus()

    def _toggle_sidebar(self) -> None:
        self.sidebar.toggle_collapse_state()
        self.sidebar_collapsed = self.sidebar.is_collapsed

    def _show_profile_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 4px; font-size: 12px; }"
        )
        menu.addAction("Lock Workstation (Ctrl+L)", self._lock_workstation)
        menu.addAction("Edit Profile & Password", self._open_edit_profile_dialog)
        menu.addAction("System Settings", lambda: self.navigate_to_route("settings"))
        menu.addSeparator()
        menu.addAction("Sign Out", self.close)
        menu.exec(self.cursor().pos())

    def _open_edit_profile_dialog(self) -> None:
        if hasattr(self, "view_settings") and hasattr(
            self.view_settings, "_on_change_password_clicked"
        ):
            self.view_settings._on_change_password_clicked()
            self._apply_user_session()

    def _auto_select_initial_engagement(self) -> None:
        try:
            firms = self.firm_service.list_firms()
            if firms:
                self.set_active_firm(firms[0].id)
            else:
                self._update_header_combo()
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
        """Legacy slot for indexed button clicks."""
        if 0 <= idx < len(NAV_ITEMS):
            attr = NAV_ITEMS[idx][0]
            route_map = {
                "btn_dashboard": "dashboard",
                "btn_pbc": "pbc",
                "btn_audit_matrix": "audit_matrix",
                "btn_financial_data": "financial_data",
                "btn_working_papers": "working_papers",
                "btn_reports": "reports",
                "btn_queries": "queries",
                "btn_documents": "documents",
                "btn_gst": "gst",
                "btn_compliance": "compliance",
                "btn_inspection": "inspection",
                "btn_ai_assistant": "ai_assistant",
                "btn_clients": "clients",
                "btn_engagements": "engagements",
                "btn_firms": "firms",
                "btn_archival": "archival",
                "btn_roll_forward": "roll_forward",
                "btn_settings": "settings",
            }
            if attr in route_map:
                self.navigate_to_route(route_map[attr])

    def _sync_views_engagement(self, eng: Any) -> None:
        views = (
            self.view_guided_workflow,
            self.view_reconciliations,
            self.view_documents,
            self.view_financial_data,
            self.view_gst,
            self.view_compliance,
            self.view_audit_matrix,
            self.view_working_papers,
            self.view_reports,
            self.view_pbc,
            self.view_queries,
            self.view_ai_assistant,
            self.view_archival,
            self.view_roll_forward,
        )
        eng_id = eng.id if hasattr(eng, "id") else eng
        for v in views:
            func = getattr(v, "set_active_engagement", None)
            if callable(func):
                func(eng_id)
        self.ai_drawer.set_engagement(eng)

    def set_active_firm(self, firm_id: str) -> None:
        firm = self.firm_service.get_firm_by_id(firm_id)
        if not firm:
            return
        self.current_firm = firm
        self.view_dashboard.set_firm(firm)
        self.view_clients.set_firm(firm)
        clients = self.client_service.list_clients_for_firm(firm.id)
        eng_found = next(
            (e for c in clients for e in self.engagement_service.list_engagements_for_client(c.id)),
            None,
        )
        if eng_found:
            self.set_active_engagement(eng_found.id)
        elif clients:
            self.set_active_client(clients[0].id)
        else:
            self.current_client, self.current_engagement = None, None
            self._update_header_combo()

    def set_active_client(self, client_id: str) -> None:
        client = self.client_service.get_client_by_id(client_id)
        if not client:
            return
        self.current_client = client
        if hasattr(self, "view_client_workspace") and self.view_client_workspace:
            self.view_client_workspace.set_client(client.id)
        if client.firm_id and (self.current_firm is None or self.current_firm.id != client.firm_id):
            parent_firm = self.firm_service.get_firm_by_id(client.firm_id)
            if parent_firm:
                self.current_firm = parent_firm
                self.view_dashboard.set_firm(parent_firm)
                self.view_clients.set_firm(parent_firm)
        engs = self.engagement_service.list_engagements_for_client(client.id)
        if engs:
            self.set_active_engagement(engs[0].id)
        else:
            self.current_engagement = None
            self._sync_views_engagement(None)
            self._update_header_combo()

    def set_active_engagement(self, engagement_id: str) -> None:
        eng = self.engagement_service.get_engagement_by_id(engagement_id)
        if not eng:
            return
        self.current_engagement = eng
        client = self.client_service.get_client_by_id(eng.client_id)
        self.current_client = client
        if client:
            parent_firm = self.firm_service.get_firm_by_id(client.firm_id)
            if parent_firm:
                self.current_firm = parent_firm
                self.view_dashboard.set_firm(parent_firm)
        self._sync_views_engagement(eng)
        self._update_header_combo()

    def _update_header_combo(self) -> None:
        self.eng_selector_combo.blockSignals(True)
        self.eng_selector_combo.clear()
        firms = self.firm_service.list_firms()
        firm_id = self.current_firm.id if self.current_firm else (firms[0].id if firms else "")
        clients = self.client_service.list_clients_for_firm(firm_id) if firm_id else []
        if not clients and hasattr(self.client_service, "list_all_clients"):
            clients = self.client_service.list_all_clients()
        if not clients:
            self.eng_selector_combo.addItem("No Clients Registered — Create Client", None)
            self.eng_selector_combo.blockSignals(False)
            return
        selected_idx, item_idx = 0, 0
        for c in clients:
            engs = self.engagement_service.list_engagements_for_client(c.id)
            if engs:
                for e in engs:
                    audit_t = (
                        e.audit_type.value if hasattr(e.audit_type, "value") else str(e.audit_type)
                    )
                    self.eng_selector_combo.addItem(
                        f"{c.name} · FY {e.financial_year} · {audit_t}", f"eng:{e.id}"
                    )
                    if self.current_engagement and e.id == self.current_engagement.id:
                        selected_idx = item_idx
                    item_idx += 1
            else:
                self.eng_selector_combo.addItem(f"{c.name} (No engagements created)", f"cli:{c.id}")
                if (
                    self.current_client
                    and c.id == self.current_client.id
                    and not self.current_engagement
                ):
                    selected_idx = item_idx
                item_idx += 1
        self.eng_selector_combo.setCurrentIndex(selected_idx)
        self.eng_selector_combo.blockSignals(False)
        if not self.current_engagement and item_idx > 0:
            first_data = self.eng_selector_combo.itemData(selected_idx)
            if first_data and str(first_data).startswith("eng:"):
                first_eng = self.engagement_service.get_engagement_by_id(str(first_data)[4:])
                if first_eng:
                    self.current_engagement = first_eng
                    self._sync_views_engagement(first_eng)

    def _on_header_engagement_changed(self, idx: int) -> None:
        data = self.eng_selector_combo.itemData(idx)
        if data is None:
            self.navigate_to_route("clients")
            return
        if data:
            if str(data).startswith("eng:"):
                self.set_active_engagement(str(data)[4:])
            elif str(data).startswith("cli:"):
                self.set_active_client(str(data)[4:])
            else:
                self.set_active_engagement(str(data))

    def _on_new_engagement(self) -> None:
        firms = self.firm_service.list_firms()
        if not firms:
            QMessageBox.warning(self, "No Firm", "Please create an Audit Firm first.")
            self.navigate_to_route("firms")
            return
        firm = self.current_firm or firms[0]
        clients = self.client_service.list_clients_for_firm(firm.id)
        if not clients:
            QMessageBox.warning(
                self, "No Client", "Please create a Client first before adding an Engagement."
            )
            self.navigate_to_route("clients")
            return
        dlg = EngagementDialog(
            self.engagement_service,
            firm=firm,
            client=self.current_client or clients[0],
            parent=self,
        )
        if dlg.exec() and dlg.result_engagement:
            if hasattr(self.working_paper_service, "scaffold_schedule_iii_working_papers"):
                self.working_paper_service.scaffold_schedule_iii_working_papers(
                    dlg.result_engagement.id
                )
            self.set_active_engagement(dlg.result_engagement.id)
            self.view_engagements.refresh()
            self.view_dashboard.refresh_dashboard()

    def _open_command_palette(self) -> None:
        from finauditpro.ui.dialogs.command_palette_dialog import CommandPaletteDialog

        db_mgr = getattr(self, "db_manager", None)
        dlg = CommandPaletteDialog(self, db_manager=db_mgr)
        dlg.action_triggered.connect(
            lambda k, p: (
                self.stack.setCurrentIndex(p)
                if isinstance(p, int) and 0 <= p < self.stack.count()
                else self.navigate_to_route(str(k))
            )
        )
        dlg.exec()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if hasattr(self, "lock_screen_widget") and self.lock_screen_widget:
            self.lock_screen_widget.setGeometry(self.rect())

    def _setup_inactivity_timer(self) -> None:
        import os
        import sys

        from PySide6.QtCore import QEvent, QObject, QTimer
        from PySide6.QtWidgets import QApplication

        timeout_env = os.environ.get("FINAUDITPRO_INACTIVITY_TIMEOUT_MS")
        if "pytest" in sys.modules and timeout_env:
            self.inactivity_timeout_ms = int(timeout_env)
        elif timeout_env:
            self.inactivity_timeout_ms = max(int(timeout_env), 60_000)
        else:
            self.inactivity_timeout_ms = 900_000

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(self.inactivity_timeout_ms)
        self.inactivity_timer.timeout.connect(self._lock_workstation)

        class InteractionFilter(QObject):
            def __init__(self, timer: QTimer) -> None:
                super().__init__()
                self.timer = timer

            def eventFilter(self, obj: QObject, event: QEvent) -> bool:
                if event.type() in (
                    QEvent.Type.MouseButtonPress,
                    QEvent.Type.MouseButtonRelease,
                    QEvent.Type.MouseMove,
                    QEvent.Type.KeyPress,
                    QEvent.Type.KeyRelease,
                    QEvent.Type.Wheel,
                ):
                    self.timer.start()
                return False

        self.interaction_filter = InteractionFilter(self.inactivity_timer)
        app_inst = QApplication.instance()
        if app_inst:
            app_inst.installEventFilter(self.interaction_filter)
        self.inactivity_timer.start()

    def _lock_workstation(self) -> None:
        """Securely lock the user session and cover the GUI with the LockScreenOverlay."""
        if hasattr(self, "lock_screen_widget") and self.lock_screen_widget:
            return
        from finauditpro.application.security.rbac import RBACManager
        from finauditpro.ui.widgets.lock_screen import LockScreenOverlay

        rbac_manager = RBACManager(self.current_user_session)
        rbac_manager.lock_session()
        self.lock_screen_widget = LockScreenOverlay(self, rbac_manager)
        self.lock_screen_widget.setGeometry(self.rect())
        self.inactivity_timer.stop()

        def on_unlocked():
            self.lock_screen_widget = None
            self.inactivity_timer.start()

        self.lock_screen_widget.unlocked.connect(on_unlocked)
        self.lock_screen_widget.show()
        self.lock_screen_widget.raise_()
