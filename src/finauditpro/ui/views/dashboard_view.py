"""
Active Engagement Audit Command Center Dashboard View for FinAuditPro.
Precision UI/UX Polish & Production-Grade Finish.
"""

from datetime import datetime

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

from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.ui.theme import CardWidget, MetricCard, StatusBadge


class DashboardView(QWidget):
    """Enterprise Audit Command Center Overview Dashboard View."""

    engagement_selected = Signal(str)
    navigate_to_clients = Signal()

    def __init__(
        self,
        firm_service: FirmService,
        client_service: ClientService,
        engagement_service: EngagementService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self.client_service = client_service
        self.engagement_service = engagement_service

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

        # 1. Page Header — strong engagement context
        hdr = QFrame()
        hdr.setStyleSheet("background: transparent; border: none;")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(0, 0, 0, 0)

        left_v = QVBoxLayout()
        left_v.setSpacing(3)

        title_lbl = QLabel("Audit Overview")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A; letter-spacing: -0.4px; border: none; background: transparent;")

        ctx_row = QHBoxLayout()
        ctx_row.setSpacing(8)
        self.lbl_context_text = QLabel("RELIANCE · FY 2025–26")
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

        self.date_lbl = QLabel(datetime.now().strftime("%d %b %Y"))
        self.date_lbl.setStyleSheet("font-size: 11px; font-weight: 500; color: #94A3B8; background: transparent; border: none;")
        hdr_l.addWidget(self.date_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        body_layout.addWidget(hdr)

        # 2. Row 1: Workflow Stepper (60%) + Needs Attention (40%)
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        ws_card = CardWidget("AUDIT WORKFLOW")
        ws_v = QVBoxLayout()
        ws_v.setSpacing(8)

        stepper = QHBoxLayout()
        stepper.setSpacing(0)
        self.steps_data = [("Client", "✓", True, False), ("FY", "✓", True, False), ("Engagement", "●", False, True), ("Materiality", "○", False, False), ("Documentation", "○", False, False), ("Completion", "○", False, False)]
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
                conn = QLabel("—")
                conn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                conn.setFixedWidth(16)
                conn.setStyleSheet("color: #CBD5E1; font-weight: 400; font-size: 10px; border: none; background: transparent;")
                stepper.addWidget(conn)

        ws_v.addLayout(stepper)

        act_frame = QFrame()
        act_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px;")
        act_l = QHBoxLayout(act_frame)
        act_l.setContentsMargins(0, 0, 0, 0)
        act_v = QVBoxLayout()
        act_v.setSpacing(2)
        act_hdr = QLabel("NEXT ACTION")
        act_hdr.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; border: none; background: transparent;")
        act_title = QLabel("Complete engagement parameters")
        act_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #0F172A; border: none; background: transparent;")
        act_desc = QLabel("Configure engagement details, statutory parameters, materiality and audit scope.")
        act_desc.setStyleSheet("font-size: 11px; color: #64748B; border: none; background: transparent;")
        act_v.addWidget(act_hdr)
        act_v.addWidget(act_title)
        act_v.addWidget(act_desc)

        btn_go = QPushButton("Continue Setup →")
        btn_go.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_go.setStyleSheet("QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 12px; font-weight: 600; border-radius: 6px; padding: 7px 14px; border: none; } QPushButton:hover { background-color: #1D4ED8; }")
        btn_go.clicked.connect(self._on_go_clients_clicked)

        act_l.addLayout(act_v)
        act_l.addStretch()
        act_l.addWidget(btn_go)
        ws_v.addWidget(act_frame)
        ws_card.content_layout.addLayout(ws_v)
        row1.addWidget(ws_card, 6)

        att_card = CardWidget("NEEDS ATTENTION")
        att_v = QVBoxLayout()
        att_v.setSpacing(4)
        self.att_row = QFrame()
        self.att_row.setStyleSheet("background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px; padding: 10px 12px;")
        att_l = QHBoxLayout(self.att_row)
        att_l.setContentsMargins(0, 0, 0, 0)
        self.att_txt = QLabel("✓  All clear — no findings require attention")
        self.att_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #15803D; border: none; background: transparent;")
        att_l.addWidget(self.att_txt)
        att_v.addWidget(self.att_row)
        att_card.content_layout.addLayout(att_v)
        row1.addWidget(att_card, 4)
        body_layout.addLayout(row1)


        # 3. Row 2: 4 KPI Cards
        stats = QHBoxLayout()
        stats.setSpacing(10)
        self.card_clients = MetricCard(
            "TOTAL CLIENTS", "0", "Registered clients", accent_color="#0284C7", action_text="View →"
        )
        self.card_completed = MetricCard(
            "COMPLETED AUDITS", "0", "This financial year", accent_color="#16A34A"
        )
        self.card_pending = MetricCard(
            "OPEN FINDINGS", "0", "No action required", accent_color="#D97706", action_text="View →"
        )
        self.card_high_risk = MetricCard(
            "HIGH RISK CASES",
            "0",
            "No high-risk exposure",
            accent_color="#DC2626",
            action_text="Review →",
        )
        stats.addWidget(self.card_clients)
        stats.addWidget(self.card_completed)
        stats.addWidget(self.card_pending)
        stats.addWidget(self.card_high_risk)
        body_layout.addLayout(stats)

        # 4. Row 3: Audit Progress + Risk Exposure
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        trend_card = CardWidget("AUDIT PROGRESS")
        trend_v = QVBoxLayout()
        trend_txt = QLabel(
            "No completed audits yet\nComplete your first engagement to begin tracking progress."
        )
        trend_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trend_txt.setStyleSheet(
            "font-size: 12px; color: #94A3B8; padding: 10px; border: none; background: transparent; line-height: 1.4;"
        )
        trend_v.addWidget(trend_txt)
        trend_card.content_layout.addLayout(trend_v)

        risk_card = CardWidget("RISK EXPOSURE")
        self.risk_v = QVBoxLayout()
        self.risk_v.setSpacing(4)
        self.lbl_zero_risk = QLabel("✓  No risk exposure identified")
        self.lbl_zero_risk.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zero_risk.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #15803D; padding: 10px; border: none; background: transparent;"
        )
        self.risk_v.addWidget(self.lbl_zero_risk)
        risk_card.content_layout.addLayout(self.risk_v)

        row3.addWidget(trend_card, 6)
        row3.addWidget(risk_card, 4)
        body_layout.addLayout(row3)

        # 5. Row 4: Recent Audit Engagements (content-driven height)
        table_card = CardWidget("RECENT AUDIT ENGAGEMENTS")
        self.table_projects = QTableWidget()
        self.table_projects.setColumnCount(6)
        self.table_projects.setHorizontalHeaderLabels(
            ["CLIENT", "FINANCIAL YEAR", "TYPE", "STATUS", "RISK", "ACTION"]
        )
        self.table_projects.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for c in range(1, 6):
            self.table_projects.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.Fixed
            )
        self.table_projects.setColumnWidth(1, 120)
        self.table_projects.setColumnWidth(2, 140)
        self.table_projects.setColumnWidth(3, 100)
        self.table_projects.setColumnWidth(4, 100)
        self.table_projects.setColumnWidth(5, 80)
        self.table_projects.verticalHeader().setVisible(False)
        self.table_projects.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_projects.setAlternatingRowColors(True)
        self.table_projects.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.table_projects.itemClicked.connect(self._on_table_click)

        table_card.content_layout.addWidget(self.table_projects)
        body_layout.addWidget(table_card)

        # Absorb remaining viewport space so cards don't stretch
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

    def refresh_dashboard(self) -> None:
        clients = self.client_service.list_clients_for_firm(self.current_firm.id) if self.current_firm else (self.client_service.list_all_clients() if hasattr(self.client_service, "list_all_clients") else [])
        self.card_clients.set_value(str(len(clients)))
        all_engagements: list[Engagement] = []
        for c in clients:
            all_engagements.extend(self.engagement_service.list_engagements_for_client(c.id))

        completed_cnt = sum(1 for e in all_engagements if str(getattr(e, "status", "")).lower() in ("completed", "signed off", "locked"))
        self.card_completed.set_value(str(completed_cnt))

        if all_engagements:
            e_active = all_engagements[0]
            c_name = next((c.name for c in clients if c.id == e_active.client_id), "—")
            audit_t = e_active.audit_type.value if hasattr(e_active.audit_type, "value") else str(e_active.audit_type)
            status_v = e_active.status.value if hasattr(e_active.status, "value") else str(e_active.status)
            self.lbl_context_text.setText(f"{c_name} · FY {e_active.financial_year}")
            self.lbl_audit_type.setText(audit_t)
            self.status_badge.setText(status_v)
        else:
            self.lbl_context_text.setText("No active engagement — Ready for setup")
            self.lbl_audit_type.setText("Statutory Audit")
            self.status_badge.setText("Setup")

        self.table_projects.setRowCount(0)
        client_map = {c.id: c.name for c in clients}

        for idx, eng in enumerate(all_engagements[:10]):
            self.table_projects.insertRow(idx)
            c_name = client_map.get(eng.client_id, "—")
            audit_t = eng.audit_type.value if hasattr(eng.audit_type, "value") else str(eng.audit_type)
            status_val = eng.status.value if hasattr(eng.status, "value") else str(eng.status)
            c_item = QTableWidgetItem(c_name)
            c_item.setData(Qt.ItemDataRole.UserRole, eng.id)

            items = [
                c_item,
                QTableWidgetItem(f"FY {eng.financial_year}"),
                QTableWidgetItem(audit_t),
                QTableWidgetItem(f"● {status_val}"),
                QTableWidgetItem("● Normal"),
                QTableWidgetItem("Open →"),
            ]
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_projects.setItem(idx, col, item)

        row_cnt = max(1, len(all_engagements[:10]))
        self.table_projects.setFixedHeight(row_cnt * 36 + 32)

    def _on_go_clients_clicked(self) -> None:
        self.navigate_to_clients.emit()


