"""
Active Engagement Dashboard View for FinAuditPro.
Enterprise Audit Overview with 6-step progress stepper, stat summary cards, and risk breakdown.
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
from finauditpro.ui.theme import CardWidget, MetricCard


class DashboardView(QWidget):
    """Primary enterprise audit overview dashboard view."""

    engagement_selected = Signal(str)  # Emits engagement_id
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
        scroll.setStyleSheet("background-color: #F5F5F7; border: none;")

        body = QWidget()
        body.setStyleSheet("background-color: #F5F5F7;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 24, 28, 28)
        body_layout.setSpacing(20)

        # 1. Page Header with Title & Date Badge
        header_row = QHBoxLayout()
        header_v = QVBoxLayout()
        header_v.setSpacing(4)

        lbl_title = QLabel("Audit Overview")
        lbl_title.setStyleSheet("font-size: 26px; font-weight: 800; color: #1D1D1F; border: none; background: transparent;")
        lbl_sub = QLabel("Monitor active engagements, statutory compliance, audit findings, and risk exposure.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #6E6E73; border: none; background: transparent;")

        header_v.addWidget(lbl_title)
        header_v.addWidget(lbl_sub)
        header_row.addLayout(header_v)
        header_row.addStretch()

        date_lbl = QLabel(datetime.now().strftime("%a, %d %b %Y"))
        date_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #007AFF; background: rgba(0, 122, 255, 0.1); padding: 6px 14px; border-radius: 8px; border: none;"
        )
        header_row.addWidget(date_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        body_layout.addLayout(header_row)

        # 2. Row 1: Active Audit Workspace Progress Panel (60%) + Needs Attention Card (40%)
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        # Active Audit Workspace Card
        ws_card = CardWidget("ACTIVE AUDIT WORKSPACE — 0% Complete")
        ws_v = QVBoxLayout()
        ws_v.setSpacing(12)

        stepper_layout = QHBoxLayout()
        stepper_layout.setSpacing(6)
        self.steps = [
            "1. Client Created",
            "2. FY Selected",
            "3. Engagement Created",
            "4. Materiality Defined",
            "5. Document Collection",
            "6. Complete",
        ]
        self.step_labels: list[QLabel] = []
        for idx, step in enumerate(self.steps):
            slbl = QLabel(step)
            slbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            is_active = (idx == 0)
            bg = "#007AFF" if is_active else "#F2F2F7"
            fg = "#FFFFFF" if is_active else "#6E6E73"
            slbl.setStyleSheet(
                f"background-color: {bg}; color: {fg}; font-size: 11px; font-weight: 700; border-radius: 6px; padding: 6px 8px; border: none;"
            )
            stepper_layout.addWidget(slbl, stretch=1)
            self.step_labels.append(slbl)

        ws_v.addLayout(stepper_layout)

        # Recommended Action Banner
        rec_banner = QFrame()
        rec_banner.setStyleSheet("background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 10px 14px;")
        rec_l = QHBoxLayout(rec_banner)
        rec_l.setContentsMargins(0, 0, 0, 0)

        rec_txt = QLabel("📌 Recommended Next Step: Initialize client engagement & statutory parameters")
        rec_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #1D4ED8; border: none; background: transparent;")

        btn_go_client = QPushButton("Go to Client Management ➔")
        btn_go_client.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_go_client.setStyleSheet(
            "QPushButton { background-color: #007AFF; color: #FFFFFF; font-size: 11px; font-weight: 700; border-radius: 6px; padding: 6px 12px; border: none; }"
            "QPushButton:hover { background-color: #0062CC; }"
        )
        btn_go_client.clicked.connect(self._on_go_clients_clicked)

        rec_l.addWidget(rec_txt)
        rec_l.addStretch()
        rec_l.addWidget(btn_go_client)
        ws_v.addWidget(rec_banner)

        ws_card.content_layout.addLayout(ws_v)
        row1.addWidget(ws_card, 6)

        # Needs Attention Card
        att_card = CardWidget("NEEDS ATTENTION")
        att_v = QVBoxLayout()
        att_v.setSpacing(8)

        att_row = QFrame()
        att_row.setStyleSheet("background-color: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 12px;")
        att_l = QHBoxLayout(att_row)
        att_l.setContentsMargins(0, 0, 0, 0)
        att_txt = QLabel("✓ All caught up — no high-priority items require immediate action.")
        att_txt.setStyleSheet("font-size: 12px; font-weight: 600; color: #047857; border: none; background: transparent;")
        att_l.addWidget(att_txt)

        att_v.addWidget(att_row)
        att_card.content_layout.addLayout(att_v)
        row1.addWidget(att_card, 4)

        body_layout.addLayout(row1)

        # 3. Row 2: 4 Key Metric Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.card_clients = MetricCard("TOTAL CLIENTS", "0", "Registered", accent_color="#0284c7")
        self.card_completed = MetricCard("COMPLETED AUDITS", "0", "This Year", accent_color="#047857")
        self.card_pending = MetricCard("OPEN FINDINGS", "0", "Action Req.", accent_color="#d97706")
        self.card_high_risk = MetricCard("HIGH RISK CASES", "0", "Flagged by AI", accent_color="#dc2626")

        stats_layout.addWidget(self.card_clients)
        stats_layout.addWidget(self.card_completed)
        stats_layout.addWidget(self.card_pending)
        stats_layout.addWidget(self.card_high_risk)
        body_layout.addLayout(stats_layout)

        # 4. Row 3: Audit Progress Trend & Risk Summary
        row3 = QHBoxLayout()
        row3.setSpacing(16)

        trend_card = CardWidget("Audit Progress Trend")
        trend_v = QVBoxLayout()
        trend_txt = QLabel("No completed audits yet\nYour audit activity and lifecycle progress trends will appear here.")
        trend_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trend_txt.setStyleSheet("font-size: 12px; color: #86868B; padding: 24px; border: none; background: transparent;")
        trend_v.addWidget(trend_txt)
        trend_card.content_layout.addLayout(trend_v)

        risk_card = CardWidget("RISK SUMMARY")
        risk_v = QVBoxLayout()
        risk_v.setSpacing(8)

        risk_items = [
            ("🔴 Critical Anomaly Findings", "0", "#DC2626"),
            ("🟡 High Exposure Findings", "0", "#D97706"),
            ("🔵 Medium Category Anomalies", "0", "#2563EB"),
            ("🟢 Low Risk Observations", "0", "#16A34A"),
        ]
        self.risk_labels: dict[str, QLabel] = {}
        for label_text, count_str, color_hex in risk_items:
            r_frame = QFrame()
            r_frame.setStyleSheet("border-bottom: 1px solid #F1F5F9; background: transparent;")
            r_layout = QHBoxLayout(r_frame)
            r_layout.setContentsMargins(4, 6, 4, 6)

            lbl_name = QLabel(label_text)
            lbl_name.setStyleSheet("font-size: 12px; font-weight: 600; color: #1E293B; border: none; background: transparent;")

            lbl_val = QLabel(count_str)
            lbl_val.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {color_hex}; border: none; background: transparent;")

            r_layout.addWidget(lbl_name)
            r_layout.addStretch()
            r_layout.addWidget(lbl_val)
            risk_v.addWidget(r_frame)
            self.risk_labels[label_text] = lbl_val

        risk_card.content_layout.addLayout(risk_v)

        row3.addWidget(trend_card, 6)
        row3.addWidget(risk_card, 4)
        body_layout.addLayout(row3)

        # 5. Row 4: Recent Audit Projects Table Card
        table_card = CardWidget("Recent Audit Projects")
        self.table_projects = QTableWidget()
        self.table_projects.setColumnCount(4)
        self.table_projects.setHorizontalHeaderLabels(["Client Name", "Financial Year", "Status", "Risk Exposure"])
        self.table_projects.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_projects.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_projects.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_projects.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_projects.setColumnWidth(1, 140)
        self.table_projects.setColumnWidth(2, 140)
        self.table_projects.setColumnWidth(3, 140)
        self.table_projects.setMinimumHeight(220)
        self.table_projects.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; border: none; gridline-color: #F2F2F7; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-size: 11px; font-weight: 800; border: none; border-bottom: 1px solid #E2E8F0; padding: 8px 12px; }
        """)

        table_card.content_layout.addWidget(self.table_projects)
        body_layout.addWidget(table_card)

        scroll.setWidget(body)
        main_layout.addWidget(scroll)

        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        if not self.current_firm:
            clients = self.client_service.list_clients() if self.client_service else []
        else:
            clients = self.client_service.list_clients_for_firm(self.current_firm.id)

        self.card_clients.set_value(str(len(clients)))

        all_engagements: list[Engagement] = []
        for c in clients:
            engs = self.engagement_service.list_engagements_for_client(c.id)
            all_engagements.extend(engs)

        completed_cnt = sum(1 for e in all_engagements if str(getattr(e, "status", "")).lower() == "completed")
        self.card_completed.set_value(str(completed_cnt))

        self.table_projects.setRowCount(0)
        client_map = {c.id: c.name for c in clients}

        for idx, eng in enumerate(all_engagements[:10]):
            self.table_projects.insertRow(idx)
            c_name = client_map.get(eng.client_id, "Unknown Client")
            item_name = QTableWidgetItem(c_name)
            item_fy = QTableWidgetItem(eng.financial_year)
            status_val = eng.status.value if hasattr(eng.status, "value") else str(eng.status)
            item_status = QTableWidgetItem(status_val)
            item_risk = QTableWidgetItem("Low Exposure")

            item_name.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item_fy.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item_status.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item_risk.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

            self.table_projects.setItem(idx, 0, item_name)
            self.table_projects.setItem(idx, 1, item_fy)
            self.table_projects.setItem(idx, 2, item_status)
            self.table_projects.setItem(idx, 3, item_risk)

    def _on_go_clients_clicked(self) -> None:
        self.navigate_to_clients.emit()
