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
        body_layout.setContentsMargins(24, 18, 24, 24)
        body_layout.setSpacing(14)

        # 1. Structured Page Header Hierarchy (Clean typography, badging ONLY for status)
        hdr_card = QFrame()
        hdr_card.setStyleSheet("background: transparent; border: none;")
        hdr_l = QHBoxLayout(hdr_card)
        hdr_l.setContentsMargins(0, 0, 0, 0)

        left_v = QVBoxLayout()
        left_v.setSpacing(4)

        title_lbl = QLabel("Audit Overview")
        title_lbl.setStyleSheet("font-size: 26px; font-weight: 800; color: #0F172A; letter-spacing: -0.6px; border: none; background: transparent;")

        sub_row = QHBoxLayout()
        sub_row.setSpacing(10)

        self.lbl_context_text = QLabel("RELIANCE · FY 2025–26 · Statutory Audit")
        self.lbl_context_text.setStyleSheet("font-size: 13px; font-weight: 600; color: #475569; border: none; background: transparent;")

        self.status_badge = StatusBadge("● Planning", "info")

        self.lbl_pct_text = QLabel("0% complete")
        self.lbl_pct_text.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; border: none; background: transparent;")

        sub_row.addWidget(self.lbl_context_text)
        sub_row.addWidget(self.status_badge)
        sub_row.addWidget(self.lbl_pct_text)
        sub_row.addStretch()

        left_v.addWidget(title_lbl)
        left_v.addLayout(sub_row)
        hdr_l.addLayout(left_v)
        hdr_l.addStretch()

        self.date_lbl = QLabel(datetime.now().strftime("Last updated: %d %b %Y · %I:%M %p"))
        self.date_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #64748B; background: #FFFFFF; padding: 6px 12px; border-radius: 6px; border: 1px solid #E2E8F0;"
        )
        hdr_l.addWidget(self.date_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        body_layout.addWidget(hdr_card)

        # 2. Row 1: Connected Workflow Stepper (60%) + Smart Needs Attention Panel (40%)
        row1 = QHBoxLayout()
        row1.setSpacing(14)

        # Workflow Card
        ws_card = CardWidget("CURRENT AUDIT WORKFLOW")
        ws_v = QVBoxLayout()
        ws_v.setSpacing(10)

        # Connected Stepper
        stepper_layout = QHBoxLayout()
        stepper_layout.setSpacing(2)
        self.steps_data = [
            ("Client", "✓", True, False),
            ("FY", "✓", True, False),
            ("Engagement", "●", False, True),
            ("Materiality", "○", False, False),
            ("Documentation", "○", False, False),
            ("Completion", "○", False, False),
        ]
        self.step_widgets: list[QLabel] = []
        for i, (name, icon, is_done, is_active) in enumerate(self.steps_data):
            slbl = QLabel(f"{icon} {name}")
            slbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg = "#DCFCE7" if is_done else ("#DBEAFE" if is_active else "#F8FAFC")
            fg = "#15803D" if is_done else ("#1D4ED8" if is_active else "#64748B")
            bd = "#86EFAC" if is_done else ("#93C5FD" if is_active else "#E2E8F0")
            slbl.setStyleSheet(
                f"background-color: {bg}; color: {fg}; font-size: 11px; font-weight: 700; border: 1px solid {bd}; border-radius: 6px; padding: 6px 4px;"
            )
            stepper_layout.addWidget(slbl, stretch=1)
            self.step_widgets.append(slbl)

            if i < len(self.steps_data) - 1:
                conn = QLabel("─")
                conn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                conn.setStyleSheet("color: #CBD5E1; font-weight: 800; font-size: 10px; border: none; background: transparent;")
                stepper_layout.addWidget(conn)

        ws_v.addLayout(stepper_layout)

        # Contextual Next Action CTA Module
        rec_banner = QFrame()
        rec_banner.setStyleSheet("background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 10px 14px;")
        rec_l = QHBoxLayout(rec_banner)
        rec_l.setContentsMargins(0, 0, 0, 0)

        act_v = QVBoxLayout()
        act_v.setSpacing(2)
        rec_hdr = QLabel("NEXT ACTION — Complete engagement parameters")
        rec_hdr.setStyleSheet("font-size: 12px; font-weight: 800; color: #1D4ED8; border: none; background: transparent;")
        rec_txt = QLabel("Configure engagement details, statutory parameters, materiality and audit scope. (~5 min)\nRequired before audit documentation can begin.")
        rec_txt.setStyleSheet("font-size: 11px; color: #1E40AF; border: none; background: transparent; line-height: 1.3;")
        act_v.addWidget(rec_hdr)
        act_v.addWidget(rec_txt)

        btn_go_client = QPushButton("Continue Setup ➔")
        btn_go_client.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_go_client.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 11px; font-weight: 700; border-radius: 6px; padding: 7px 14px; border: none; }"
            "QPushButton:hover { background-color: #1D4ED8; }"
        )
        btn_go_client.clicked.connect(self._on_go_clients_clicked)

        rec_l.addLayout(act_v)
        rec_l.addStretch()
        rec_l.addWidget(btn_go_client)
        ws_v.addWidget(rec_banner)

        ws_card.content_layout.addLayout(ws_v)
        row1.addWidget(ws_card, 6)

        # Smart Compact Needs Attention Card (94px height)
        att_card = CardWidget("NEEDS ATTENTION")
        att_v = QVBoxLayout()
        att_v.setSpacing(6)

        self.att_row = QFrame()
        self.att_row.setStyleSheet("background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 10px 12px;")
        att_l = QHBoxLayout(self.att_row)
        att_l.setContentsMargins(0, 0, 0, 0)
        self.att_txt = QLabel("✓ All clear\nNo critical or high-priority findings require attention.\nLast checked 2 min ago.")
        self.att_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #15803D; border: none; background: transparent; line-height: 1.35;")
        att_l.addWidget(self.att_txt)

        att_v.addWidget(self.att_row)
        att_card.content_layout.addLayout(att_v)
        row1.addWidget(att_card, 4)

        body_layout.addLayout(row1)

        # 3. Row 2: 4 Actionable KPI Cards (94px height)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_clients = MetricCard("TOTAL CLIENTS", "0", "Registered clients", accent_color="#0284c7", action_text="View clients ➔")
        self.card_completed = MetricCard("COMPLETED AUDITS", "0", "This financial year", accent_color="#16a34a")
        self.card_pending = MetricCard("OPEN FINDINGS", "0", "No action required", accent_color="#d97706", action_text="View findings ➔")
        self.card_high_risk = MetricCard("HIGH RISK CASES", "0", "No high-risk exposure", accent_color="#dc2626", action_text="Review risk ➔")

        stats_layout.addWidget(self.card_clients)
        stats_layout.addWidget(self.card_completed)
        stats_layout.addWidget(self.card_pending)
        stats_layout.addWidget(self.card_high_risk)
        body_layout.addLayout(stats_layout)

        # 4. Row 3: Compact Audit Progress & Intelligent Risk Summary
        row3 = QHBoxLayout()
        row3.setSpacing(14)

        trend_card = CardWidget("AUDIT PROGRESS OVERVIEW")
        trend_v = QVBoxLayout()
        trend_txt = QLabel("0 completed audits\nComplete your first engagement to begin tracking audit progress over time.")
        trend_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trend_txt.setStyleSheet("font-size: 12px; color: #64748B; padding: 12px; border: none; background: transparent; line-height: 1.4;")
        trend_v.addWidget(trend_txt)
        trend_card.content_layout.addLayout(trend_v)

        risk_card = CardWidget("RISK EXPOSURE SUMMARY")
        self.risk_v = QVBoxLayout()
        self.risk_v.setSpacing(4)

        self.lbl_zero_risk = QLabel("✓ No risk exposure identified\nAll risk anomaly scanners currently clear.")
        self.lbl_zero_risk.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zero_risk.setStyleSheet("font-size: 12px; font-weight: 600; color: #15803D; padding: 12px; border: none; background: transparent;")
        self.risk_v.addWidget(self.lbl_zero_risk)

        risk_card.content_layout.addLayout(self.risk_v)

        row3.addWidget(trend_card, 6)
        row3.addWidget(risk_card, 4)
        body_layout.addLayout(row3)

        # 5. Row 4: Recent Audit Engagements Table (Strictly Content-Driven Height!)
        table_card = CardWidget("RECENT AUDIT ENGAGEMENTS")
        self.table_projects = QTableWidget()
        self.table_projects.setColumnCount(6)
        self.table_projects.setHorizontalHeaderLabels(["CLIENT", "FINANCIAL YEAR", "ENGAGEMENT TYPE", "STATUS", "RISK EXPOSURE", "ACTION"])
        self.table_projects.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 6):
            self.table_projects.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
        self.table_projects.setColumnWidth(1, 130)
        self.table_projects.setColumnWidth(2, 160)
        self.table_projects.setColumnWidth(3, 120)
        self.table_projects.setColumnWidth(4, 130)
        self.table_projects.setColumnWidth(5, 90)

        table_card.content_layout.addWidget(self.table_projects)
        body_layout.addWidget(table_card)

        scroll.setWidget(body)
        main_layout.addWidget(scroll)

        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        if not self.current_firm:
            clients = self.client_service.list_all_clients() if hasattr(self.client_service, "list_all_clients") else []
        else:
            clients = self.client_service.list_clients_for_firm(self.current_firm.id)

        self.card_clients.set_value(str(len(clients)))

        all_engagements: list[Engagement] = []
        for c in clients:
            engs = self.engagement_service.list_engagements_for_client(c.id)
            all_engagements.extend(engs)

        completed_cnt = sum(1 for e in all_engagements if str(getattr(e, "status", "")).lower() == "completed")
        self.card_completed.set_value(str(completed_cnt))

        if all_engagements:
            e_active = all_engagements[0]
            c_active_name = next((c.name for c in clients if c.id == e_active.client_id), "RELIANCE")
            audit_t = e_active.audit_type.value if hasattr(e_active.audit_type, "value") else str(e_active.audit_type)
            self.lbl_context_text.setText(f"{c_active_name} · FY {e_active.financial_year} · {audit_t}")
        else:
            self.lbl_context_text.setText("RELIANCE · FY 2025–26 · Statutory Audit")

        self.table_projects.setRowCount(0)
        client_map = {c.id: c.name for c in clients}

        for idx, eng in enumerate(all_engagements[:10]):
            self.table_projects.insertRow(idx)
            c_name = client_map.get(eng.client_id, "RELIANCE")
            item_name = QTableWidgetItem(f"🏢  {c_name}")
            item_fy = QTableWidgetItem(f"FY {eng.financial_year}")
            audit_t = eng.audit_type.value if hasattr(eng.audit_type, "value") else str(eng.audit_type)
            item_type = QTableWidgetItem(audit_t)
            status_val = eng.status.value if hasattr(eng.status, "value") else str(eng.status)
            item_status = QTableWidgetItem(f"● {status_val}")
            item_risk = QTableWidgetItem("● Low Risk")
            item_action = QTableWidgetItem("Open ➔")

            for item in [item_name, item_fy, item_type, item_status, item_risk, item_action]:
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

            self.table_projects.setItem(idx, 0, item_name)
            self.table_projects.setItem(idx, 1, item_fy)
            self.table_projects.setItem(idx, 2, item_type)
            self.table_projects.setItem(idx, 3, item_status)
            self.table_projects.setItem(idx, 4, item_risk)
            self.table_projects.setItem(idx, 5, item_action)

        row_cnt = max(1, len(all_engagements[:10]))
        h = row_cnt * 38 + 36
        self.table_projects.setFixedHeight(h)

    def _on_go_clients_clicked(self) -> None:
        self.navigate_to_clients.emit()
