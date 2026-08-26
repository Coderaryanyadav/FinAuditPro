"""Main Application Shell Window for FinAuditPro Enterprise Audit Operating System."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
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
from finauditpro.application.services.audit_query_service import AuditQueryService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_request_service import DocumentRequestService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.ui.dialogs.engagement_dialog import EngagementDialog
from finauditpro.ui.dialogs.login_dialog import LoginDialog
from finauditpro.ui.styles import GLOBAL_QSS
from finauditpro.ui.views.ai_assistant_view import AIAssistantView
from finauditpro.ui.views.ai_copilot_drawer import AICopilotDrawer
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
from finauditpro.ui.views.pbc_tracker_view import PBCTrackerView
from finauditpro.ui.views.report_view import ReportView
from finauditpro.ui.views.roll_forward_view import RollForwardView
from finauditpro.ui.views.settings_view import SettingsView
from finauditpro.ui.views.working_paper_view import WorkingPaperView

NAV_ITEMS = [
    ("btn_dashboard", "📊 Command Center", "WORKSPACE"),
    ("btn_pbc", "① Intake & PBC", "GUIDED PIPELINE"),
    ("btn_audit_matrix", "② Planning & SA 320", "GUIDED PIPELINE"),
    ("btn_financial_data", "③ TB/GL & Scrutiny", "GUIDED PIPELINE"),
    ("btn_working_papers", "④ Working Papers", "GUIDED PIPELINE"),
    ("btn_reports", "⑤ Reports & Sign-Off", "GUIDED PIPELINE"),
    ("btn_queries", "💬 Client Queries", "FIELDWORK TOOLS"),
    ("btn_documents", "📁 Uploaded Evidence", "FIELDWORK TOOLS"),
    ("btn_gst", "⚡ GST 2B Reconciler", "FIELDWORK TOOLS"),
    ("btn_compliance", "⚖️ Compliance Checklist", "FIELDWORK TOOLS"),
    ("btn_ai_assistant", "✨ AI Copilot Lab", "FIELDWORK TOOLS"),
    ("btn_clients", "🏢 Clients", "ADMINISTRATION"),
    ("btn_engagements", "📋 Engagements", "ADMINISTRATION"),
    ("btn_firms", "🏛️ Audit Firms", "ADMINISTRATION"),
    ("btn_archival", "🔒 Archival & Sealing", "SYSTEM"),
    ("btn_roll_forward", "🔄 Roll-Forward Tie-Out", "SYSTEM"),
    ("btn_settings", "⚙️ Settings", "SYSTEM"),
]

GUIDED_STEPS = [
    ("1. Intake & PBC", "btn_pbc"), ("2. Planning (SA 320)", "btn_audit_matrix"),
    ("3. TB/GL Scrutiny", "btn_financial_data"), ("4. Workpapers", "btn_working_papers"),
    ("5. Report & Sign-Off", "btn_reports"),
]


def _tag(w: Any, name: str) -> Any:
    w.setObjectName(name)
    return w


class MainWindow(QMainWindow):
    """Main Application Shell Window for FinAuditPro Enterprise Audit Operating System."""

    def __init__(self, firm_service: Any = None, client_service: Any = None, engagement_service: Any = None, document_service: Any = None, financial_data_service: Any = None, audit_matrix_service: Any = None, working_paper_service: Any = None, report_service: Any = None, ai_service: Any = None, archival_repo: Any = None, roll_forward_repo: Any = None, db_manager: Any = None) -> None:
        super().__init__()
        db = firm_service if hasattr(firm_service, "session_scope") else (db_manager if hasattr(db_manager, "session_scope") else None)
        if db:
            from finauditpro.application.services.ai_service import AIService
            self.firm_service, self.client_service = FirmService(db), ClientService(db)
            self.engagement_service, self.document_service = EngagementService(db), DocumentService(db)
            self.financial_data_service, self.audit_matrix_service = FinancialDataService(db), AuditMatrixService(db)
            self.working_paper_service, self.report_service, self.ai_service = WorkingPaperService(db), ReportService(db), AIService(db)
            self.pbc_service, self.query_service = DocumentRequestService(db), AuditQueryService(db)
        else:
            self.firm_service, self.client_service, self.engagement_service, self.document_service = firm_service, client_service, engagement_service, document_service
            self.financial_data_service, self.audit_matrix_service, self.working_paper_service, self.report_service, self.ai_service = financial_data_service, audit_matrix_service, working_paper_service, report_service, ai_service
            self.pbc_service, self.query_service = DocumentRequestService(firm_service.db_manager), AuditQueryService(firm_service.db_manager)

        self.archival_repo, self.roll_forward_repo, self.db_manager = archival_repo, roll_forward_repo, db
        self.current_firm: Firm | None = None
        self.current_client: Client | None = None
        self.current_engagement: Engagement | None = None
        self.sidebar_collapsed = False
        self.pipeline_btns: list[QPushButton] = []
        self.setWindowTitle("FinAuditPro — Guided Statutory Audit Operating System")
        self.resize(1440, 920); self.setStyleSheet(GLOBAL_QSS)
        self._init_ui(); self._show_login_flow(); self._auto_select_initial_engagement()

    @property
    def active_engagement_id(self) -> str | None:
        return self.current_engagement.id if self.current_engagement else None

    def _show_login_flow(self) -> None:
        import sys
        if "pytest" not in sys.modules: LoginDialog(self).exec()

    def _init_ui(self) -> None:
        central = _tag(QWidget(), "appBg"); self.setCentralWidget(central)
        main_layout = QHBoxLayout(central); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # 1. Sidebar
        self.sidebar = _tag(QFrame(), "dashboardSidebar"); self.sidebar.setFixedWidth(230)
        sb_layout = QVBoxLayout(self.sidebar); sb_layout.setContentsMargins(10, 14, 10, 14); sb_layout.setSpacing(3)
        logo_row = QHBoxLayout()
        logo_box = _tag(QLabel("FA"), "sidebarLogoBadge"); logo_box.setFixedSize(30, 30); logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_name = _tag(QLabel("FinAuditPro"), "sidebarAppTitle")
        self.btn_collapse = QPushButton("◀"); self.btn_collapse.setFixedSize(24, 24); self.btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_collapse.setStyleSheet("QPushButton { border: none; background: transparent; color: #64748B; font-size: 11px; font-weight: 600; }")
        self.btn_collapse.clicked.connect(self._toggle_sidebar)
        for w in (logo_box, self.logo_name): logo_row.addWidget(w)
        logo_row.addStretch(); logo_row.addWidget(self.btn_collapse)
        sb_layout.addLayout(logo_row); sb_layout.addSpacing(8)

        self.btn_group = QButtonGroup(self)
        cur_sec = None
        for idx, (attr, title, sec) in enumerate(NAV_ITEMS):
            if sec != cur_sec:
                cur_sec = sec; sb_layout.addWidget(_tag(QLabel(sec), "sidebarSectionLabel"))
            btn = _tag(QPushButton(title), "navButton"); btn.setCheckable(True)
            setattr(self, attr, btn); self.btn_group.addButton(btn, idx); sb_layout.addWidget(btn)
        self.btn_dashboard.setChecked(True); sb_layout.addStretch()

        prof = _tag(QFrame(), "sidebarProfileFrame"); pf_l = QHBoxLayout(prof); pf_l.setContentsMargins(4, 8, 4, 4)
        av = _tag(QLabel("CA"), "userAvatar"); av.setFixedSize(28, 28); av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        u_info = QVBoxLayout(); u_info.setSpacing(0); u_info.addWidget(_tag(QLabel("Partner"), "userName")); u_info.addWidget(_tag(QLabel("Chartered Accountant"), "userRole"))
        btn_more = QPushButton("•••"); btn_more.setFixedSize(22, 22); btn_more.setStyleSheet("QPushButton { border: none; background: transparent; color: #64748B; font-weight: 600; }")
        btn_more.clicked.connect(self._show_profile_menu)
        for w in (av,): pf_l.addWidget(w)
        pf_l.addLayout(u_info); pf_l.addStretch(); pf_l.addWidget(btn_more); sb_layout.addWidget(prof)
        main_layout.addWidget(self.sidebar)

        # 2. Main Workspace Right Container
        right_container = QWidget(); rc_layout = QVBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0); rc_layout.setSpacing(0)

        # Header Bar
        header = _tag(QFrame(), "dashboardHeader"); header.setFixedHeight(56)
        h_layout = QHBoxLayout(header); h_layout.setContentsMargins(20, 0, 20, 0)
        search_frame = _tag(QFrame(), "globalSearchFrame"); sf_l = QHBoxLayout(search_frame); sf_l.setContentsMargins(10, 4, 10, 4)
        sf_s = _tag(QLineEdit(), "globalSearchInput"); sf_s.setPlaceholderText("Quick Search (⌘P)..."); sf_s.setReadOnly(True); sf_s.setCursor(Qt.CursorShape.PointingHandCursor)
        sf_s.mousePressEvent = lambda e: self._open_command_palette()
        sf_l.addWidget(sf_s); sf_l.addWidget(_tag(QLabel("⌘P"), "globalShortcutBadge")); h_layout.addWidget(search_frame); h_layout.addStretch()

        act_lbl = QLabel("ACTIVE AUDIT:"); act_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #94A3B8; letter-spacing: 0.5px;")
        self.eng_selector_combo = _tag(QComboBox(), "clientSelectorCombo"); self.eng_selector_combo.setMinimumWidth(280)
        self.eng_selector_combo.currentIndexChanged.connect(self._on_header_engagement_changed)
        btn_new_audit = _tag(QPushButton("+ New Engagement"), "primaryBtn"); btn_new_audit.clicked.connect(self._on_new_engagement)
        self.btn_copilot_toggle = QPushButton("✨ AI Copilot")
        self.btn_copilot_toggle.setStyleSheet("QPushButton { background: #1e293b; color: #38bdf8; border: 1px solid #0284c7; border-radius: 6px; padding: 6px 14px; font-weight: 600; font-size: 13px; } QPushButton:hover { background: #0369a1; color: #ffffff; }")
        self.btn_copilot_toggle.clicked.connect(self._toggle_ai_drawer)
        for hw in (act_lbl, self.eng_selector_combo): h_layout.addWidget(hw)
        h_layout.addSpacing(6); h_layout.addWidget(btn_new_audit); h_layout.addSpacing(6); h_layout.addWidget(self.btn_copilot_toggle)
        rc_layout.addWidget(header)

        # Guided Pipeline Ribbon
        pipeline_bar = QFrame(); pipeline_bar.setFixedHeight(38); pipeline_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        p_layout = QHBoxLayout(pipeline_bar); p_layout.setContentsMargins(18, 0, 18, 0); p_layout.setSpacing(6)
        p_lbl = QLabel("AUDIT PIPELINE:"); p_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B; letter-spacing: 0.5px;"); p_layout.addWidget(p_lbl)
        self.pipeline_btns = []
        for step_name, btn_attr in GUIDED_STEPS:
            pbtn = QPushButton(step_name); pbtn.setCursor(Qt.CursorShape.PointingHandCursor)
            pbtn.setStyleSheet("QPushButton { background: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 500; } QPushButton:hover { background: #EFF6FF; color: #2563EB; border-color: #93C5FD; }")
            pbtn.clicked.connect(lambda _, a=btn_attr: getattr(self, a).click())
            self.pipeline_btns.append(pbtn); p_layout.addWidget(pbtn)
            if step_name != GUIDED_STEPS[-1][0]:
                arr = QLabel("➔"); arr.setStyleSheet("color: #CBD5E1; font-size: 9px; font-weight: bold;"); p_layout.addWidget(arr)
        p_layout.addStretch(); rc_layout.addWidget(pipeline_bar)

        # 3. Stacked Views & AI Drawer
        body_layout = QHBoxLayout(); body_layout.setContentsMargins(0, 0, 0, 0); body_layout.setSpacing(0)
        self.stack = QStackedWidget(); self._init_views(); body_layout.addWidget(self.stack, stretch=1)
        self.ai_drawer = AICopilotDrawer(self.ai_service, parent=self); self.ai_drawer.setVisible(False); self.ai_drawer.closed.connect(lambda: self.ai_drawer.setVisible(False))
        body_layout.addWidget(self.ai_drawer); rc_layout.addLayout(body_layout, stretch=1); main_layout.addWidget(right_container, stretch=1)
        self.btn_group.idClicked.connect(self._on_nav_clicked)
        QShortcut(QKeySequence("Ctrl+K"), self, self._toggle_ai_drawer); QShortcut(QKeySequence("Meta+K"), self, self._toggle_ai_drawer)

    def _init_views(self) -> None:
        self.view_dashboard = DashboardView(self.firm_service, self.client_service, self.engagement_service, self.audit_matrix_service)
        self.view_dashboard.navigate_to_clients.connect(lambda: self.btn_clients.click()); self.view_dashboard.navigate_to_engagements.connect(lambda: self.btn_engagements.click()); self.view_dashboard.navigate_to_matrix.connect(lambda: self.btn_audit_matrix.click()); self.view_dashboard.engagement_selected.connect(self.set_active_engagement)
        self.view_firms, self.view_clients = FirmView(self.firm_service), ClientView(self.firm_service, self.client_service)
        self.view_firms.firm_selected.connect(self.set_active_firm); self.view_firms.firm_changed.connect(self._on_firms_changed); self.view_clients.client_selected.connect(self.set_active_client); self.view_clients.client_changed.connect(self._on_clients_changed)
        self.view_engagements = EngagementView(self.firm_service, self.client_service, self.engagement_service)
        self.view_engagements.engagement_changed.connect(self.set_active_engagement); self.view_engagements.engagement_selected.connect(self.set_active_engagement)
        self.view_documents, self.view_financial_data = DocumentView(self.document_service), FinancialDataView(self.financial_data_service, self.engagement_service)
        self.view_gst, self.view_compliance, self.view_audit_matrix = GSTVerificationView(), ComplianceView(), AuditMatrixView(self.audit_matrix_service)
        self.view_ai_assistant = AIAssistantView(self.ai_service, self.document_service, self.engagement_service)
        self.view_working_papers, self.view_reports = WorkingPaperView(self.engagement_service, self.working_paper_service), ReportView(self.engagement_service, self.report_service)
        self.view_pbc, self.view_queries = PBCTrackerView(self.pbc_service), AuditQueryView(self.query_service)
        self.view_archival, self.view_roll_forward, self.view_settings = ArchivalView(self.db_manager), RollForwardView(self.db_manager), SettingsView()

        views = (
            self.view_dashboard, self.view_pbc, self.view_audit_matrix, self.view_financial_data,
            self.view_working_papers, self.view_reports, self.view_queries, self.view_documents,
            self.view_gst, self.view_compliance, self.view_ai_assistant, self.view_clients,
            self.view_engagements, self.view_firms, self.view_archival, self.view_roll_forward, self.view_settings
        )
        for v in views: self.stack.addWidget(v)

    def _toggle_ai_drawer(self) -> None:
        self.ai_drawer.setVisible(not self.ai_drawer.isVisible())
        if self.ai_drawer.isVisible(): self.ai_drawer.inp_query.setFocus()

    def _toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        self.sidebar.setFixedWidth(64 if self.sidebar_collapsed else 230)
        self.logo_name.setVisible(not self.sidebar_collapsed)
        self.btn_collapse.setText("▶" if self.sidebar_collapsed else "◀")

    def _show_profile_menu(self) -> None:
        menu = QMenu(self); menu.setStyleSheet("QMenu { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 4px; font-size: 12px; }")
        menu.addAction("Firm Settings", lambda: self.btn_settings.click()); menu.addSeparator(); menu.addAction("Sign Out", self.close); menu.exec(self.cursor().pos())

    def _auto_select_initial_engagement(self) -> None:
        try:
            firms = self.firm_service.list_firms()
            if firms: self.set_active_firm(firms[0].id)
            else: self._update_header_combo()
        except Exception: pass

    def _on_firms_changed(self) -> None:
        self._update_header_combo(); self.view_dashboard.refresh_dashboard()

    def _on_clients_changed(self) -> None:
        self._update_header_combo(); self.view_dashboard.refresh_dashboard(); self.view_engagements.refresh()

    def _on_nav_clicked(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        current_nav = NAV_ITEMS[idx][0] if 0 <= idx < len(NAV_ITEMS) else ""
        for i, (_, attr) in enumerate(GUIDED_STEPS):
            if attr == current_nav:
                self.pipeline_btns[i].setStyleSheet("QPushButton { background: #2563EB; color: #FFFFFF; border: 1px solid #1D4ED8; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 600; }")
            else:
                self.pipeline_btns[i].setStyleSheet("QPushButton { background: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; border-radius: 4px; padding: 3px 8px; font-size: 12px; font-weight: 500; } QPushButton:hover { background: #EFF6FF; color: #2563EB; border-color: #93C5FD; }")

    def _sync_views_engagement(self, eng: Any) -> None:
        views = (
            self.view_documents, self.view_financial_data, self.view_gst, self.view_compliance,
            self.view_audit_matrix, self.view_working_papers, self.view_reports,
            self.view_pbc, self.view_queries, self.view_ai_assistant, self.view_archival, self.view_roll_forward
        )
        eng_id = eng.id if hasattr(eng, "id") else eng
        for v in views:
            func = getattr(v, "set_active_engagement", None)
            if callable(func): func(eng_id)
        self.ai_drawer.set_engagement(eng)

    def set_active_firm(self, firm_id: str) -> None:
        firm = self.firm_service.get_firm_by_id(firm_id)
        if not firm: return
        self.current_firm = firm; self.view_dashboard.set_firm(firm); self.view_clients.set_firm(firm)
        clients = self.client_service.list_clients_for_firm(firm.id)
        eng_found = next((e for c in clients for e in self.engagement_service.list_engagements_for_client(c.id)), None)
        if eng_found: self.set_active_engagement(eng_found.id)
        elif clients: self.set_active_client(clients[0].id)
        else: self.current_client, self.current_engagement = None, None; self._update_header_combo()

    def set_active_client(self, client_id: str) -> None:
        client = self.client_service.get_client_by_id(client_id)
        if not client: return
        self.current_client = client
        if client.firm_id and (self.current_firm is None or self.current_firm.id != client.firm_id):
            parent_firm = self.firm_service.get_firm_by_id(client.firm_id)
            if parent_firm:
                self.current_firm = parent_firm; self.view_dashboard.set_firm(parent_firm); self.view_clients.set_firm(parent_firm)
        engs = self.engagement_service.list_engagements_for_client(client.id)
        if engs: self.set_active_engagement(engs[0].id)
        else: self.current_engagement = None; self._sync_views_engagement(None); self._update_header_combo()

    def set_active_engagement(self, engagement_id: str) -> None:
        eng = self.engagement_service.get_engagement_by_id(engagement_id)
        if not eng: return
        self.current_engagement = eng; client = self.client_service.get_client_by_id(eng.client_id); self.current_client = client
        if client:
            parent_firm = self.firm_service.get_firm_by_id(client.firm_id)
            if parent_firm: self.current_firm = parent_firm; self.view_dashboard.set_firm(parent_firm)
        self._sync_views_engagement(eng); self._update_header_combo()

    def _update_header_combo(self) -> None:
        self.eng_selector_combo.blockSignals(True); self.eng_selector_combo.clear()
        firms = self.firm_service.list_firms(); firm_id = self.current_firm.id if self.current_firm else (firms[0].id if firms else "")
        clients = self.client_service.list_clients_for_firm(firm_id) if firm_id else []
        if not clients and hasattr(self.client_service, "list_all_clients"): clients = self.client_service.list_all_clients()
        if not clients:
            self.eng_selector_combo.addItem("No Clients Registered — Create Client", None); self.eng_selector_combo.blockSignals(False); return
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
        self.eng_selector_combo.setCurrentIndex(selected_idx); self.eng_selector_combo.blockSignals(False)
        if not self.current_engagement and item_idx > 0:
            first_data = self.eng_selector_combo.itemData(selected_idx)
            if first_data and str(first_data).startswith("eng:"):
                first_eng = self.engagement_service.get_engagement_by_id(str(first_data)[4:])
                if first_eng: self.current_engagement = first_eng; self._sync_views_engagement(first_eng)

    def _on_header_engagement_changed(self, idx: int) -> None:
        data = self.eng_selector_combo.itemData(idx)
        if data:
            if str(data).startswith("eng:"): self.set_active_engagement(str(data)[4:])
            elif str(data).startswith("cli:"): self.set_active_client(str(data)[4:])
            else: self.set_active_engagement(str(data))

    def _on_new_engagement(self) -> None:
        firms = self.firm_service.list_firms()
        if not firms:
            QMessageBox.warning(self, "No Firm", "Please create an Audit Firm first."); self.btn_firms.click(); return
        firm = self.current_firm or firms[0]; clients = self.client_service.list_clients_for_firm(firm.id)
        if not clients:
            QMessageBox.warning(self, "No Client", "Please create a Client first before adding an Engagement."); self.btn_clients.click(); return
        dlg = EngagementDialog(self.engagement_service, firm=firm, client=self.current_client or clients[0], parent=self)
        if dlg.exec() and dlg.result_engagement:
            if hasattr(self.working_paper_service, "scaffold_schedule_iii_working_papers"):
                self.working_paper_service.scaffold_schedule_iii_working_papers(dlg.result_engagement.id)
            self.set_active_engagement(dlg.result_engagement.id); self.view_engagements.refresh(); self.view_dashboard.refresh_dashboard()

    def _open_command_palette(self) -> None:
        from finauditpro.ui.dialogs.command_palette_dialog import CommandPaletteDialog
        dlg = CommandPaletteDialog(self); dlg.action_triggered.connect(lambda k, p: self.stack.setCurrentIndex(p) if k == "nav" and 0 <= p < self.stack.count() else None); dlg.exec()
