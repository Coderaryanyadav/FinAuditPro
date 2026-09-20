"""Operational Practice Command Center Overview Dashboard View for FinAuditPro.

Single-pane-of-glass practice operational dashboard providing real-time visibility into attention items,
client PBC requests, active engagements, audit activity timeline, and quick actions.
"""

from typing import Any

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

from finauditpro.application.dtos_dashboard import (
    AttentionItemDTO,
    PracticeDashboardSummaryDTO,
)
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.practice_dashboard_service import PracticeDashboardService
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, MetricCard, StatusBadge


class DashboardView(QWidget):
    """Enterprise Operational Practice Command Center Dashboard View."""

    engagement_selected = Signal(str)
    navigate_to_clients = Signal()
    navigate_to_engagements = Signal()
    navigate_to_matrix = Signal()
    navigate_to_pbc = Signal()
    navigate_to_documents = Signal()
    navigate_to_working_papers = Signal()
    navigate_to_reports = Signal()
    navigate_to_route = Signal(str)

    def __init__(
        self,
        firm_service: FirmService,
        client_service: ClientService,
        engagement_service: EngagementService,
        audit_matrix_service: AuditMatrixService,
        practice_dashboard_service: PracticeDashboardService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self.client_service = client_service
        self.engagement_service = engagement_service
        self.audit_matrix_service = audit_matrix_service

        db_manager = getattr(firm_service, "db_manager", None)
        if not practice_dashboard_service and db_manager:
            practice_dashboard_service = PracticeDashboardService(db_manager)

        self.dashboard_service = practice_dashboard_service
        self.current_firm: Firm | None = None
        self.current_client: Client | None = None
        self.current_engagement: Engagement | None = None
        self.current_summary: PracticeDashboardSummaryDTO | None = None

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
        body_layout.setSpacing(16)

        # 1. Header Bar
        hdr = QFrame()
        hdr.setStyleSheet("background: transparent; border: none;")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(0, 0, 0, 0)

        left_v = QVBoxLayout()
        left_v.setSpacing(3)
        title_lbl = QLabel("Practice Command Center")
        title_lbl.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #0F172A; border: none; background: transparent;"
        )

        ctx_row = QHBoxLayout()
        ctx_row.setSpacing(8)
        self.lbl_firm_name = QLabel("CA Practice Overview")
        self.lbl_firm_name.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #334155; border: none; background: transparent;"
        )
        self.status_badge = StatusBadge("Active Practice", "success")

        ctx_row.addWidget(self.lbl_firm_name)
        ctx_row.addWidget(self.status_badge)
        ctx_row.addStretch()

        left_v.addWidget(title_lbl)
        left_v.addLayout(ctx_row)
        hdr_l.addLayout(left_v)
        hdr_l.addStretch()

        dt_badge = QFrame()
        dt_badge.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 10px; }"
        )
        dt_l = QHBoxLayout(dt_badge)
        dt_l.setContentsMargins(0, 0, 0, 0)
        dt_l.setSpacing(6)
        self.date_lbl = QLabel(utc_now().strftime("%a, %d %b %Y"))
        self.date_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #334155; border: none; background: transparent;"
        )
        dt_l.addWidget(self.date_lbl)
        hdr_l.addWidget(dt_badge, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        body_layout.addWidget(hdr)

        # 2. Practice Quick Actions Bar
        actions_card = CardWidget("PRACTICE QUICK ACTIONS")
        act_l = QHBoxLayout()
        act_l.setSpacing(8)

        btn_add_client = QPushButton("+ New Client")
        btn_add_client.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_client.setStyleSheet(
            "QPushButton { background: #0284C7; color: #FFFFFF; font-weight: 600; font-size: 12px; border-radius: 5px; padding: 6px 12px; border: none; }"
            "QPushButton:hover { background: #0369A1; }"
        )
        btn_add_client.clicked.connect(lambda: self.navigate_to_clients.emit())

        btn_add_eng = QPushButton("+ New Engagement")
        btn_add_eng.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_eng.setStyleSheet(
            "QPushButton { background: #0F172A; color: #FFFFFF; font-weight: 600; font-size: 12px; border-radius: 5px; padding: 6px 12px; border: none; }"
            "QPushButton:hover { background: #1E293B; }"
        )
        btn_add_eng.clicked.connect(lambda: self.navigate_to_engagements.emit())

        btn_upload_docs = QPushButton("📤 Upload Evidence")
        btn_upload_docs.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upload_docs.setStyleSheet(
            "QPushButton { background: #F8FAFC; color: #334155; font-weight: 600; font-size: 12px; border-radius: 5px; padding: 6px 12px; border: 1px solid #CBD5E1; }"
            "QPushButton:hover { background: #EFF6FF; color: #2563EB; border-color: #93C5FD; }"
        )
        btn_upload_docs.clicked.connect(lambda: self.navigate_to_documents.emit())

        btn_new_req = QPushButton("📋 New Client Request")
        btn_new_req.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_req.setStyleSheet(
            "QPushButton { background: #F8FAFC; color: #334155; font-weight: 600; font-size: 12px; border-radius: 5px; padding: 6px 12px; border: 1px solid #CBD5E1; }"
            "QPushButton:hover { background: #EFF6FF; color: #2563EB; border-color: #93C5FD; }"
        )
        btn_new_req.clicked.connect(lambda: self.navigate_to_pbc.emit())

        btn_open_audit = QPushButton("⚡ Open Current Engagement")
        btn_open_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_audit.setStyleSheet(
            "QPushButton { background: #15803D; color: #FFFFFF; font-weight: 600; font-size: 12px; border-radius: 5px; padding: 6px 12px; border: none; }"
            "QPushButton:hover { background: #166534; }"
        )
        btn_open_audit.clicked.connect(lambda: self.navigate_to_matrix.emit())

        act_l.addWidget(btn_add_client)
        act_l.addWidget(btn_add_eng)
        act_l.addWidget(btn_upload_docs)
        act_l.addWidget(btn_new_req)
        act_l.addStretch()
        act_l.addWidget(btn_open_audit)

        actions_card.content_layout.addLayout(act_l)
        body_layout.addWidget(actions_card)

        # 3. Practice Metric Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_clients = MetricCard(
            "TOTAL CLIENTS", "0", "Registered clients", accent_color="#0284C7", action_text="Manage →"
        )
        self.card_clients.clicked.connect(lambda: self.navigate_to_clients.emit())

        self.card_active = MetricCard(
            "ACTIVE AUDITS", "0", "In-progress statutory engagements", accent_color="#0F172A", action_text="View →"
        )
        self.card_active.clicked.connect(lambda: self.navigate_to_engagements.emit())

        self.card_completed = MetricCard(
            "COMPLETED AUDITS", "0", "Signed-off statutory audits", accent_color="#16A34A"
        )

        self.card_attention = MetricCard(
            "ATTENTION ITEMS", "0", "Requiring auditor action", accent_color="#DC2626", action_text="Review →"
        )
        self.card_attention.clicked.connect(lambda: self.navigate_to_matrix.emit())

        for card_w in (self.card_clients, self.card_active, self.card_completed, self.card_attention):
            stats_layout.addWidget(card_w, stretch=1)

        body_layout.addLayout(stats_layout)

        # 4. Row: Today / Needs Attention Grid & PBC Request Tracker
        row_att = QHBoxLayout()
        row_att.setSpacing(12)

        # Attention Items Card
        self.att_card = CardWidget("TODAY / ATTENTION REQUIRED")
        self.att_layout = QVBoxLayout()
        self.att_layout.setSpacing(8)

        self.att_empty = EmptyStateWidget(
            title="All Clear — No Attention Required",
            description="No pending PBC document requests, open review notes, or critical findings require immediate attention.",
        )
        self.att_layout.addWidget(self.att_empty)
        self.att_card.content_layout.addLayout(self.att_layout)

        # PBC Document Request Tracker Card
        self.pbc_card = CardWidget("CLIENT DOCUMENT REQUEST STATUS")
        self.pbc_layout = QVBoxLayout()
        self.pbc_layout.setSpacing(8)

        self.pbc_empty = EmptyStateWidget(
            title="No Client PBC Requests Active",
            description="Create a client document request (PBC) to track incoming evidence documents.",
            action_text="+ Create Request",
            action_callback=lambda: self.navigate_to_pbc.emit(),
        )
        self.pbc_layout.addWidget(self.pbc_empty)
        self.pbc_card.content_layout.addLayout(self.pbc_layout)

        row_att.addWidget(self.att_card, stretch=6)
        row_att.addWidget(self.pbc_card, stretch=4)
        body_layout.addLayout(row_att)

        # 5. Active Clients & Engagements Table
        table_card = CardWidget("ACTIVE CLIENTS & ENGAGEMENT STATUS")
        self.table_clients = QTableWidget()
        self.table_clients.setColumnCount(7)
        self.table_clients.setHorizontalHeaderLabels(
            ["CLIENT NAME", "INDUSTRY", "FINANCIAL YEAR", "TYPE", "STATUS", "RISK", "ACTION"]
        )
        self.table_clients.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c, w in enumerate([110, 110, 120, 100, 80, 90], start=1):
            self.table_clients.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
            self.table_clients.setColumnWidth(c, w)

        self.table_clients.verticalHeader().setVisible(False)
        self.table_clients.setAlternatingRowColors(True)
        self.table_clients.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_clients.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.table_clients.itemClicked.connect(self._on_table_client_click)

        self.table_empty = EmptyStateWidget(
            title="No Active Clients Registered",
            description="Register audit clients and statutory engagements to begin managing practice fieldwork.",
            action_text="+ Create Client",
            action_callback=lambda: self.navigate_to_clients.emit(),
        )

        table_card.content_layout.addWidget(self.table_clients)
        table_card.content_layout.addWidget(self.table_empty)
        body_layout.addWidget(table_card)

        # 6. Row: Recent Activity Feed & Reconciliation Exceptions
        row_act = QHBoxLayout()
        row_act.setSpacing(12)

        # Recent Activity Card
        act_card = CardWidget("RECENT PRACTICE AUDIT ACTIVITY")
        self.act_layout = QVBoxLayout()
        self.act_layout.setSpacing(6)

        self.act_empty = EmptyStateWidget(
            title="No Recent Audit Activity Logs",
            description="Audit events and working paper activity will be recorded here automatically.",
        )
        self.act_layout.addWidget(self.act_empty)
        act_card.content_layout.addLayout(self.act_layout)

        # Reconciliation Exceptions Card
        recon_card = CardWidget("RECONCILIATION EXCEPTIONS")
        self.recon_layout = QVBoxLayout()
        self.recon_layout.setSpacing(6)

        self.recon_empty = EmptyStateWidget(
            title="No Reconciliation Mismatches",
            description="GSTR-2B vs GL reconciliations have zero identified discrepancies.",
        )
        self.recon_layout.addWidget(self.recon_empty)
        recon_card.content_layout.addLayout(self.recon_layout)

        row_act.addWidget(act_card, stretch=6)
        row_act.addWidget(recon_card, stretch=4)
        body_layout.addLayout(row_act)

        body_layout.addStretch(1)
        scroll.setWidget(body)
        main_layout.addWidget(scroll)

        self.refresh_dashboard()

    def _on_table_client_click(self, item: QTableWidgetItem) -> None:
        row = item.row()
        client_item = self.table_clients.item(row, 0)
        if client_item:
            eng_id = client_item.data(Qt.ItemDataRole.UserRole)
            if eng_id:
                self.engagement_selected.emit(eng_id)
                self.navigate_to_matrix.emit()

    def refresh_dashboard(self) -> None:
        """Fetches operational metrics via PracticeDashboardService and renders the UI."""
        firm_id = self.current_firm.id if self.current_firm else None

        if self.dashboard_service:
            summary = self.dashboard_service.get_practice_summary(firm_id=firm_id)
        else:
            summary = self._fallback_legacy_summary()

        self.current_summary = summary
        self.lbl_firm_name.setText(summary.firm_name)

        # 1. Update Metric Cards
        self.card_clients.set_value(str(summary.total_clients))
        self.card_active.set_value(str(summary.active_engagements))
        self.card_completed.set_value(str(summary.completed_audits))
        self.card_attention.set_value(str(len(summary.attention_items)))

        # 2. Render Attention Items Grid
        self._render_attention_items(summary.attention_items)

        # 3. Render Client Request Tracker
        self._render_client_requests(summary.client_request_statuses)

        # 4. Render Active Clients Matrix
        self._render_active_clients(summary.active_clients)

        # 5. Render Recent Activities
        self._render_recent_activities(summary.recent_activities)

        # 6. Render Reconciliation Exceptions
        self._render_reconciliation_exceptions(summary.reconciliation_exceptions)

    def _render_attention_items(self, items: list[AttentionItemDTO]) -> None:
        # Clear existing dynamic widgets in att_layout
        while self.att_layout.count() > 0:
            w = self.att_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not items:
            self.att_empty = EmptyStateWidget(
                title="All Clear — No Attention Required",
                description="No pending PBC document requests, open review notes, or critical findings require immediate attention.",
            )
            self.att_layout.addWidget(self.att_empty)
            return

        for item in items:
            frame = QFrame()
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            border_color = "#DC2626" if item.urgency == "critical" else "#D97706"
            bg_color = "#FEF2F2" if item.urgency == "critical" else "#FFFBEB"
            frame.setStyleSheet(
                f"QFrame {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 8px 12px; }}"
                f"QFrame:hover {{ background-color: #FFFFFF; }}"
            )

            f_l = QHBoxLayout(frame)
            f_l.setContentsMargins(0, 0, 0, 0)
            f_l.setSpacing(10)

            badge = QLabel("⚠️" if item.urgency == "critical" else "⚡")
            badge.setFixedSize(24, 24)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

            v_info = QVBoxLayout()
            v_info.setSpacing(2)
            lbl_title = QLabel(item.title)
            lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A; border: none; background: transparent;")
            lbl_desc = QLabel(item.description)
            lbl_desc.setStyleSheet("font-size: 11px; color: #475569; border: none; background: transparent;")

            v_info.addWidget(lbl_title)
            v_info.addWidget(lbl_desc)

            btn_action = QPushButton("Action →")
            btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_action.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #2563EB; font-weight: 600; font-size: 11px; border: 1px solid #BFDBFE; border-radius: 4px; padding: 4px 8px; }"
                "QPushButton:hover { background: #2563EB; color: #FFFFFF; }"
            )
            btn_action.clicked.connect(lambda _, r=item.target_route: self.navigate_to_route.emit(r))

            f_l.addWidget(badge)
            f_l.addLayout(v_info, stretch=1)
            f_l.addWidget(btn_action)

            self.att_layout.addWidget(frame)

    def _render_client_requests(self, requests: list[Any]) -> None:
        while self.pbc_layout.count() > 0:
            w = self.pbc_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not requests:
            self.pbc_empty = EmptyStateWidget(
                title="No Client Requests Active",
                description="Create a client document request (PBC) to track incoming evidence documents.",
                action_text="+ Create Request",
                action_callback=lambda: self.navigate_to_pbc.emit(),
            )
            self.pbc_layout.addWidget(self.pbc_empty)
            return

        for req in requests:
            frame = QFrame()
            frame.setStyleSheet("QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; }")
            f_l = QVBoxLayout(frame)
            f_l.setSpacing(4)

            top_row = QHBoxLayout()
            c_name = QLabel(getattr(req, "client_name", "Client"))
            c_name.setStyleSheet("font-weight: 600; font-size: 12px; color: #0F172A;")
            p_text = QLabel(f"{getattr(req, 'total_received', 0)}/{getattr(req, 'total_requested', 0)} received")
            p_text.setStyleSheet("font-size: 11px; font-weight: 600; color: #0284C7;")

            top_row.addWidget(c_name)
            top_row.addStretch()
            top_row.addWidget(p_text)
            f_l.addLayout(top_row)

            # Progress bar frame
            pb_frame = QFrame()
            pb_frame.setFixedHeight(6)
            pb_frame.setStyleSheet("background: #E2E8F0; border-radius: 3px;")
            pb_fill = QFrame(pb_frame)
            pct = getattr(req, "percentage_received", 0)
            pb_fill.setGeometry(0, 0, int(200 * (pct / 100)), 6)
            pb_fill.setStyleSheet("background: #0284C7; border-radius: 3px;")

            f_l.addWidget(pb_frame)
            self.pbc_layout.addWidget(frame)

    def _render_active_clients(self, active_clients: list[Any]) -> None:
        self.table_clients.setRowCount(0)
        has_clients = len(active_clients) > 0
        self.table_clients.setVisible(has_clients)
        self.table_empty.setVisible(not has_clients)

        if not has_clients:
            return

        for idx, client_summary in enumerate(active_clients[:10]):
            self.table_clients.insertRow(idx)
            c_name_item = QTableWidgetItem(client_summary.client_name)
            if client_summary.engagement_id:
                c_name_item.setData(Qt.ItemDataRole.UserRole, client_summary.engagement_id)

            risk_str = f"● {client_summary.risk_level}"
            items = [
                c_name_item,
                QTableWidgetItem(client_summary.industry or "Corporate"),
                QTableWidgetItem(f"FY {client_summary.financial_year}"),
                QTableWidgetItem(client_summary.audit_type),
                QTableWidgetItem(f"● {client_summary.status}"),
                QTableWidgetItem(risk_str),
                QTableWidgetItem("Open →"),
            ]
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_clients.setItem(idx, col, item)

        self.table_clients.setFixedHeight(len(active_clients[:10]) * 36 + 32)

    def _render_recent_activities(self, activities: list[Any]) -> None:
        while self.act_layout.count() > 0:
            w = self.act_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not activities:
            self.act_empty = EmptyStateWidget(
                title="No Recent Audit Activity Logs",
                description="Audit events and working paper activity will be recorded here automatically.",
            )
            self.act_layout.addWidget(self.act_empty)
            return

        for act in activities[:6]:
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = QLabel("•")
            dot.setStyleSheet("color: #0284C7; font-weight: 800; font-size: 14px;")
            desc = QLabel(act.description)
            desc.setStyleSheet("font-size: 12px; color: #334155;")
            desc.setWordWrap(True)

            row.addWidget(dot)
            row.addWidget(desc, stretch=1)
            self.act_layout.addLayout(row)

    def _render_reconciliation_exceptions(self, exceptions: list[Any]) -> None:
        while self.recon_layout.count() > 0:
            w = self.recon_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not exceptions:
            self.recon_empty = EmptyStateWidget(
                title="No Reconciliation Mismatches",
                description="GSTR-2B vs GL reconciliations have zero identified discrepancies.",
            )
            self.recon_layout.addWidget(self.recon_empty)
            return

        for exc in exceptions:
            lbl = QLabel(f"⚠️ {exc.title}: {exc.mismatch_count} discrepancy item(s)")
            lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #DC2626;")
            self.recon_layout.addWidget(lbl)

    def _fallback_legacy_summary(self) -> PracticeDashboardSummaryDTO:
        return PracticeDashboardSummaryDTO(
            firm_id=None,
            firm_name="CA Practice",
            total_clients=0,
            active_engagements=0,
            completed_audits=0,
        )
