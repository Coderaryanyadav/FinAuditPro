"""
Active Engagement Audit Command Center Dashboard View for FinAuditPro.
Precision UI/UX Polish & Production-Grade Finish.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.ui.theme import CardWidget, MetricCard, StatusBadge


class DashboardView(QWidget):
    """Enterprise Audit Command Center Overview Dashboard View."""
    engagement_selected = Signal(str)
    navigate_to_clients = Signal()
    navigate_to_engagements = Signal()
    navigate_to_matrix = Signal()
    def __init__(
        self,
        firm_service: FirmService,
        client_service: ClientService,
        engagement_service: EngagementService,
        audit_matrix_service: AuditMatrixService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self.client_service = client_service
        self.engagement_service = engagement_service
        self.audit_matrix_service = audit_matrix_service
        self.current_firm: Firm | None = None
        self.current_client: Client | None = None
        self.current_engagement: Engagement | None = None
        self._init_ui()
    def set_firm(self, firm: Firm | None) -> None:
        self.current_firm = firm
        self.refresh_dashboard()
    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #F8FAFC; border: none;")
        body = QWidget()
        body.setStyleSheet("background-color: #F8FAFC;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 16, 24, 24)
        body_layout.setSpacing(12)
        hdr = QFrame()
        hdr.setStyleSheet("background: transparent; border: none;")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(0, 0, 0, 0)
        left_v = QVBoxLayout()
        left_v.setSpacing(3)
        title_lbl = QLabel("Audit Overview")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A; border: none; background: transparent;")
        ctx_row = QHBoxLayout()
        ctx_row.setSpacing(8)
        self.lbl_context_text = QLabel("AUDIT OVERVIEW - FY 2025-26")
        self.lbl_context_text.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155; border: none; background: transparent;")
        self.lbl_audit_type = QLabel("Statutory Audit")
        self.lbl_audit_type.setStyleSheet("font-size: 13px; font-weight: 500; color: #64748B; border: none; background: transparent;")
        self.status_badge = StatusBadge("Planning", "info")
        self.lbl_pct_text = QLabel("0% complete")
        self.lbl_pct_text.setStyleSheet("font-size: 12px; font-weight: 500; color: #94A3B8; border: none; background: transparent;")
        for w in (self.lbl_context_text, self.lbl_audit_type, self.status_badge, self.lbl_pct_text):
            ctx_row.addWidget(w)
        ctx_row.addStretch()
        left_v.addWidget(title_lbl)
        left_v.addLayout(ctx_row)
        hdr_l.addLayout(left_v)
        hdr_l.addStretch()
        dt_badge = QFrame(); dt_badge.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 10px; }")
        dt_l = QHBoxLayout(dt_badge); dt_l.setContentsMargins(0, 0, 0, 0); dt_l.setSpacing(6)
        self.date_lbl = QLabel(utc_now().strftime("%a, %d %b %Y")); self.date_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155; border: none; background: transparent;")
        dt_l.addWidget(self.date_lbl)
        hdr_l.addWidget(dt_badge, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight); body_layout.addWidget(hdr)
        row1 = QHBoxLayout(); row1.setSpacing(12)
        ws_card = CardWidget("AUDIT WORKFLOW"); ws_v = QVBoxLayout(); ws_v.setSpacing(8)
        stepper = QHBoxLayout(); stepper.setSpacing(0)
        self.steps_data = [("Client", "", True, False), ("FY", "", True, False), ("Engagement", "●", False, True), ("Materiality", "○", False, False), ("Documentation", "○", False, False), ("Completion", "○", False, False)]
        self.step_widgets: list[QLabel] = []
        for i, (name, icon, is_done, is_active) in enumerate(self.steps_data):
            slbl = QLabel(f"{icon}  {name}")
            slbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg = "#F0FDF4" if is_done else ("#EFF6FF" if is_active else "#F8FAFC")
            fg = "#15803D" if is_done else ("#1D4ED8" if is_active else "#94A3B8")
            bd = "#BBF7D0" if is_done else ("#BFDBFE" if is_active else "#E2E8F0")
            fw = "600" if (is_done or is_active) else "500"
            slbl.setStyleSheet(f"background-color: {bg}; color: {fg}; font-size: 11px; font-weight: {fw}; border: 1px solid {bd}; border-radius: 4px; padding: 5px 2px;")
            stepper.addWidget(slbl, stretch=1)
            self.step_widgets.append(slbl)
            if i < len(self.steps_data) - 1:
                conn = QFrame()
                conn.setFixedSize(16, 2)
                conn.setStyleSheet("background-color: #CBD5E1; border: none;")
                stepper.addWidget(conn)
        ws_v.addLayout(stepper)
        act_frame = QFrame()
        act_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px;")
        act_l = QHBoxLayout(act_frame)
        act_l.setContentsMargins(0, 0, 0, 0)
        act_v = QVBoxLayout()
        act_v.setSpacing(2)
        act_hdr = QLabel("NEXT ACTION")
        act_hdr.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; border: none; background: transparent;")
        self.act_title = QLabel("Register your first audit client")
        self.act_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A; border: none; background: transparent;")
        self.act_desc = QLabel("Add a client entity to begin statutory audit planning, materiality assessment, and ledger scrutiny.")
        self.act_desc.setStyleSheet("font-size: 13px; color: #64748B; border: none; background: transparent;")
        act_v.addWidget(act_hdr)
        act_v.addWidget(self.act_title)
        act_v.addWidget(self.act_desc)
        self.btn_go = QPushButton("Create Client →")
        self.btn_go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_go.setStyleSheet("QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 12px; font-weight: 600; border-radius: 6px; padding: 7px 14px; border: 1px solid transparent; } QPushButton:hover { background-color: #1D4ED8; }")
        self.btn_go.clicked.connect(self._on_continue_setup_clicked)
        act_l.addLayout(act_v)
        act_l.addStretch()
        act_l.addWidget(self.btn_go)
        ws_v.addWidget(act_frame)
        ws_card.content_layout.addLayout(ws_v)
        row1.addWidget(ws_card, 6)
        att_card = CardWidget("NEEDS ATTENTION")
        att_v = QVBoxLayout()
        att_v.setContentsMargins(0, 4, 0, 4)
        att_v.setSpacing(6)
        self.att_row = QFrame()
        self.att_row.setStyleSheet(
            "QFrame { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px 14px; }"
        )
        att_l = QHBoxLayout(self.att_row)
        att_l.setContentsMargins(0, 0, 0, 0)
        att_l.setSpacing(10)
        self.att_dot = QLabel("✓")
        self.att_dot.setFixedSize(24, 24)
        self.att_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.att_dot.setStyleSheet("font-size: 14px; font-weight: 700; color: #16A34A; background: #DCFCE7; border-radius: 12px;")
        self.att_txt = QLabel("All clear — no open findings or critical items require attention")
        self.att_txt.setStyleSheet("font-size: 13px; font-weight: 500; color: #334155; border: none; background: transparent;")
        self.att_txt.setWordWrap(True)
        att_l.addStretch()
        att_l.addWidget(self.att_dot, alignment=Qt.AlignmentFlag.AlignVCenter)
        att_l.addWidget(self.att_txt, alignment=Qt.AlignmentFlag.AlignVCenter)
        att_l.addStretch()
        att_v.addWidget(self.att_row)
        att_card.content_layout.addLayout(att_v)
        row1.addWidget(att_card, 4)
        body_layout.addLayout(row1)
        stats = QHBoxLayout(); stats.setSpacing(12)
        self.card_clients = MetricCard("TOTAL CLIENTS", "0", "Registered clients", accent_color="#0284C7", action_text="View →")
        self.card_clients.clicked.connect(lambda: self.navigate_to_clients.emit())
        self.card_completed = MetricCard("COMPLETED AUDITS", "0", "This financial year", accent_color="#16A34A")
        self.card_pending = MetricCard("OPEN FINDINGS", "0", "No action required", accent_color="#D97706", action_text="View →")
        self.card_pending.clicked.connect(lambda: self.navigate_to_matrix.emit())
        self.card_high_risk = MetricCard("HIGH RISK CASES", "0", "No high-risk exposure", accent_color="#DC2626", action_text="Review →")
        self.card_high_risk.clicked.connect(lambda: self.navigate_to_matrix.emit())
        for card_w in (self.card_clients, self.card_completed, self.card_pending, self.card_high_risk):
            stats.addWidget(card_w, stretch=1)
        body_layout.addLayout(stats)
        row3 = QHBoxLayout(); row3.setSpacing(12)
        trend_card = CardWidget("AUDIT PROGRESS"); trend_v = QVBoxLayout()
        trend_txt = QLabel("No completed audits yet\nComplete your first engagement to begin tracking progress.")
        trend_txt.setAlignment(Qt.AlignmentFlag.AlignCenter); trend_txt.setStyleSheet("font-size: 12px; color: #94A3B8; padding: 10px; border: none; background: transparent; line-height: 1.4;")
        trend_v.addWidget(trend_txt); trend_card.content_layout.addLayout(trend_v)
        risk_card = CardWidget("RISK EXPOSURE"); self.risk_v = QVBoxLayout(); self.risk_v.setSpacing(4)
        self.lbl_zero_risk = QLabel(" No risk exposure identified")
        self.lbl_zero_risk.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_zero_risk.setStyleSheet("font-size: 12px; font-weight: 600; color: #15803D; padding: 10px; border: none; background: transparent;")
        self.risk_v.addWidget(self.lbl_zero_risk); risk_card.content_layout.addLayout(self.risk_v)
        row3.addWidget(trend_card, 6); row3.addWidget(risk_card, 4); body_layout.addLayout(row3)
        table_card = CardWidget("RECENT AUDIT ENGAGEMENTS")
        self.table_projects = QTableWidget(); self.table_projects.setColumnCount(6)
        self.table_projects.setHorizontalHeaderLabels(["CLIENT", "FINANCIAL YEAR", "TYPE", "STATUS", "RISK", "ACTION"])
        self.table_projects.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c, w in enumerate([120, 140, 100, 100, 80], start=1):
            self.table_projects.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
            self.table_projects.setColumnWidth(c, w)
        self.table_projects.verticalHeader().setVisible(False); self.table_projects.setAlternatingRowColors(True)
        self.table_projects.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_projects.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.table_projects.itemClicked.connect(self._on_table_click); self.table_projects.setVisible(False)
        from finauditpro.ui.theme import EmptyStateWidget
        self.recent_empty = EmptyStateWidget(
            title="No audit engagements registered",
            description="Create your first client and statutory engagement to begin executing audit workflows.",
            action_text="+ Create Client / Engagement",
            action_callback=self._on_continue_setup_clicked,
        )
        table_card.content_layout.addWidget(self.table_projects)
        table_card.content_layout.addWidget(self.recent_empty)
        body_layout.addWidget(table_card)
        body_layout.addStretch(1)
        scroll.setWidget(body)
        main_layout.addWidget(scroll)
        self.refresh_dashboard()
    def _on_table_click(self, item: QTableWidgetItem) -> None:
        row = item.row()
        name_item = self.table_projects.item(row, 0)
        if name_item:
            eng_id = name_item.data(Qt.ItemDataRole.UserRole)
            if eng_id:
                self.engagement_selected.emit(eng_id)
                self.navigate_to_matrix.emit()
    def _on_continue_setup_clicked(self) -> None:
        if self.current_engagement:
            self.navigate_to_matrix.emit()
        elif self.current_client:
            self.navigate_to_engagements.emit()
        else:
            self.navigate_to_clients.emit()
    def refresh_dashboard(self) -> None:
        clients = self.client_service.list_clients_for_firm(self.current_firm.id) if self.current_firm else (self.client_service.list_all_clients() if hasattr(self.client_service, "list_all_clients") else [])
        self.card_clients.set_value(str(len(clients)))
        all_engagements: list[Engagement] = []
        for c in clients:
            all_engagements.extend(self.engagement_service.list_engagements_for_client(c.id))
        completed_cnt = sum(1 for e in all_engagements if str(getattr(e, "status", "")).lower() in ("completed", "signed off", "locked"))
        self.card_completed.set_value(str(completed_cnt))
        total_open_findings = 0
        total_high_risk = 0
        has_risk_exposure = False
        for eng in all_engagements:
            findings = self.audit_matrix_service.list_findings_for_engagement(eng.id)
            total_open_findings += sum(1 for f in findings if getattr(f, "status", "") != "Closed")
            risks = self.audit_matrix_service.list_risks_for_engagement(eng.id)
            for rk in risks:
                has_risk_exposure = True
                if getattr(rk.inherent_risk, "value", str(rk.inherent_risk)).lower() == "high":
                    total_high_risk += 1
        self.card_pending.set_value(str(total_open_findings))
        self.card_high_risk.set_value(str(total_high_risk))
        if has_risk_exposure:
            self.lbl_zero_risk.setText(f"{total_high_risk} high-risk areas identified")
            self.lbl_zero_risk.setStyleSheet("font-size: 12px; font-weight: 600; color: #DC2626; padding: 10px; border: none; background: transparent;")
        else:
            self.lbl_zero_risk.setText(" No risk exposure identified")
            self.lbl_zero_risk.setStyleSheet("font-size: 12px; font-weight: 600; color: #15803D; padding: 10px; border: none; background: transparent;")
        step_active_idx = 0
        if not clients:
            self.lbl_context_text.setText("No active engagement — Ready for setup")
            self.lbl_audit_type.setText("Statutory Audit")
            self.status_badge.setText("Setup")
            self.act_title.setText("Register your first audit client")
            self.act_desc.setText("Add a client entity to begin statutory audit planning, materiality assessment, and ledger scrutiny.")
            self.btn_go.setText("+ Create Client →")
            step_active_idx = 0
        elif not all_engagements:
            self.lbl_context_text.setText(f"{clients[0].name} — Ready to create engagement")
            self.lbl_audit_type.setText("Statutory Audit")
            self.status_badge.setText("Setup")
            self.act_title.setText("Create an engagement for " + clients[0].name)
            self.act_desc.setText("Set up the financial year, audit scope, and statutory terms to activate audit tools.")
            self.btn_go.setText("+ Create Engagement →")
            step_active_idx = 2
        else:
            e_active = self.current_engagement or all_engagements[0]
            c_name = next((c.name for c in clients if c.id == e_active.client_id), "—")
            audit_t = e_active.audit_type.value if hasattr(e_active.audit_type, "value") else str(e_active.audit_type)
            status_v = e_active.status.value if hasattr(e_active.status, "value") else str(e_active.status)
            self.lbl_context_text.setText(f"{c_name} · FY {e_active.financial_year}")
            self.lbl_audit_type.setText(audit_t)
            self.status_badge.setText(status_v)
            mat = self.audit_matrix_service.get_latest_materiality(e_active.id) if hasattr(self.audit_matrix_service, "get_latest_materiality") else None
            if not mat:
                step_active_idx = 3
                self.act_title.setText(f"Set materiality benchmark for {c_name}")
                self.act_desc.setText("Calculate overall & performance materiality (SA 320) to establish testing thresholds.")
                self.btn_go.setText("Calculate Materiality →")
            elif status_v.lower() in ("completed", "signed off", "locked"):
                step_active_idx = 5
                self.act_title.setText(f"Audit completed for {c_name}")
                self.act_desc.setText("All procedures concluded, reports generated, and working papers sealed.")
                self.btn_go.setText("View Final Reports →")
            else:
                step_active_idx = 4
                self.act_title.setText(f"Execute audit procedures for {c_name}")
                self.act_desc.setText("Review risks, execute substantive test procedures, and inspect working papers.")
                self.btn_go.setText("Open Audit Matrix →")
        step_names = ["Client", "FY", "Engagement", "Materiality", "Documentation", "Completion"]
        for i, slbl in enumerate(self.step_widgets):
            is_done = i < step_active_idx
            is_active = i == step_active_idx
            s_name = step_names[i] if i < len(step_names) else ""
            prefix = "✓ " if is_done else ("● " if is_active else "○ ")
            slbl.setText(f"{prefix}{s_name}")
            bg = "#F0FDF4" if is_done else ("#EFF6FF" if is_active else "#F8FAFC")
            fg = "#15803D" if is_done else ("#1D4ED8" if is_active else "#94A3B8")
            bd = "#BBF7D0" if is_done else ("#BFDBFE" if is_active else "#E2E8F0")
            fw = "600" if (is_done or is_active) else "500"
            slbl.setStyleSheet(f"background-color: {bg}; color: {fg}; font-size: 11px; font-weight: {fw}; border: 1px solid {bd}; border-radius: 4px; padding: 5px 2px;")
        self.table_projects.setRowCount(0)
        client_map = {c.id: c.name for c in clients}
        for idx, eng in enumerate(all_engagements[:10]):
            self.table_projects.insertRow(idx)
            c_name = client_map.get(eng.client_id, "—")
            audit_t = eng.audit_type.value if hasattr(eng.audit_type, "value") else str(eng.audit_type)
            status_val = eng.status.value if hasattr(eng.status, "value") else str(eng.status)
            c_item = QTableWidgetItem(c_name)
            c_item.setData(Qt.ItemDataRole.UserRole, eng.id)
            eng_risks = self.audit_matrix_service.list_risks_for_engagement(eng.id)
            if any(getattr(r.inherent_risk, "value", str(r.inherent_risk)).lower() == "high" for r in eng_risks):
                risk_lbl = "● High"
            elif any(getattr(r.inherent_risk, "value", str(r.inherent_risk)).lower() == "medium" for r in eng_risks):
                risk_lbl = "● Medium"
            else:
                risk_lbl = "● Normal"
            items = [
                c_item,
                QTableWidgetItem(f"FY {eng.financial_year}"),
                QTableWidgetItem(audit_t),
                QTableWidgetItem(f"● {status_val}"),
                QTableWidgetItem(risk_lbl),
                QTableWidgetItem("Open →"),
            ]
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_projects.setItem(idx, col, item)
        has_eng = len(all_engagements) > 0
        self.table_projects.setVisible(has_eng)
        self.recent_empty.setVisible(not has_eng)
        if has_eng:
            self.table_projects.setFixedHeight(len(all_engagements[:10]) * 36 + 32)
