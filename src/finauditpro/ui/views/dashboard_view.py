"""Active Engagement Dashboard View for FinAuditPro."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
    """Primary engagement dashboard view."""

    engagement_selected = Signal(str)  # Emits engagement_id

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

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. Active Context Banner Card
        self.context_card = CardWidget()
        ctx_layout = QHBoxLayout()
        ctx_layout.setContentsMargins(0, 0, 0, 0)

        info_box = QVBoxLayout()
        self.ctx_title = QLabel("NO ACTIVE ENGAGEMENT SELECTED")
        self.ctx_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #38bdf8;")

        self.ctx_sub = QLabel(
            "Select or create a firm, client, and engagement to begin audit work."
        )
        self.ctx_sub.setStyleSheet("font-size: 13px; color: #94a3b8;")

        info_box.addWidget(self.ctx_title)
        info_box.addWidget(self.ctx_sub)
        ctx_layout.addLayout(info_box, stretch=1)

        # Engagement Selector Combo
        sel_box = QVBoxLayout()
        sel_lbl = QLabel("Switch Active Engagement:")
        sel_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")

        self.eng_selector_combo = QComboBox()
        self.eng_selector_combo.setMinimumWidth(260)
        self.eng_selector_combo.currentIndexChanged.connect(self._on_engagement_combo_changed)

        sel_box.addWidget(sel_lbl)
        sel_box.addWidget(self.eng_selector_combo)
        ctx_layout.addLayout(sel_box)

        self.context_card.content_layout.addLayout(ctx_layout)
        main_layout.addWidget(self.context_card)

        # 2. KPI Metric Cards Layout
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self.card_clients = MetricCard(
            "Total Clients", "0", "Registered clients", accent_color="#0284c7"
        )
        self.card_active_eng = MetricCard(
            "Active Engagements", "0", "In progress audits", accent_color="#38bdf8"
        )
        self.card_completed_eng = MetricCard(
            "Completed Audits", "0", "Signed-off engagements", accent_color="#10b981"
        )
        self.card_findings = MetricCard(
            "Open Exceptions", "0", "Audit exceptions & findings", accent_color="#f59e0b"
        )

        kpi_layout.addWidget(self.card_clients)
        kpi_layout.addWidget(self.card_active_eng)
        kpi_layout.addWidget(self.card_completed_eng)
        kpi_layout.addWidget(self.card_findings)

        main_layout.addLayout(kpi_layout)

        # 3. Workflow Progress Card
        wf_card = CardWidget("Audit Workflow Stage Progress")
        wf_layout = QHBoxLayout()
        wf_layout.setSpacing(10)

        self.stages = [
            "1. Planning",
            "2. Doc Collection",
            "3. Financial Data",
            "4. Audit Procedures",
            "5. Review",
            "6. Reporting",
        ]
        self.stage_widgets: list[QLabel] = []

        for stage in self.stages:
            lbl = QLabel(stage)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #121418;
                    color: #64748b;
                    border: 1px solid #2e3440;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-weight: 600;
                    font-size: 11px;
                }
            """)
            wf_layout.addWidget(lbl, stretch=1)
            self.stage_widgets.append(lbl)

        wf_card.content_layout.addLayout(wf_layout)
        main_layout.addWidget(wf_card)

        # 4. Recent Activity Stream Card
        act_card = CardWidget("Audit System Activity Log")
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(3)
        self.activity_table.setHorizontalHeaderLabels(["Timestamp (UTC)", "Action", "Details"])
        self.activity_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.activity_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.activity_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setMinimumHeight(180)

        act_card.content_layout.addWidget(self.activity_table)
        main_layout.addWidget(act_card)

        main_layout.addStretch()

    def refresh(self, active_engagement_id: str | None = None) -> None:
        """Reload dashboard stats, context, and engagement list."""
        summary = self.engagement_service.get_dashboard_summary(
            firm_id=self.current_firm.id if self.current_firm else None
        )

        self.card_clients.set_value(str(summary.total_clients))
        self.card_active_eng.set_value(str(summary.active_engagements))
        self.card_completed_eng.set_value(str(summary.completed_engagements))
        self.card_findings.set_value(str(summary.open_findings))

        # Populate selector combo
        all_engagements = self.engagement_service.list_all_engagements()
        self.eng_selector_combo.blockSignals(True)
        self.eng_selector_combo.clear()
        self.eng_selector_combo.addItem("-- Select Engagement --", None)

        selected_idx = 0
        for i, eng in enumerate(all_engagements, start=1):
            try:
                client = self.client_service.get_client(eng.client_id)
                label = f"{client.name} | {eng.audit_type.value} ({eng.financial_year})"
            except Exception:
                label = f"Engagement {eng.id[:8]} ({eng.financial_year})"

            self.eng_selector_combo.addItem(label, eng.id)
            if active_engagement_id and eng.id == active_engagement_id:
                selected_idx = i

        self.eng_selector_combo.setCurrentIndex(selected_idx)
        self.eng_selector_combo.blockSignals(False)

        if active_engagement_id:
            self._set_active_engagement(active_engagement_id)
        elif all_engagements:
            self._set_active_engagement(all_engagements[0].id)
        else:
            self._clear_active_context()

        # Update Activity Log Table
        self.activity_table.setRowCount(0)
        for row, act in enumerate(summary.recent_activities):
            self.activity_table.insertRow(row)
            self.activity_table.setItem(row, 0, QTableWidgetItem(act["timestamp"]))
            self.activity_table.setItem(row, 1, QTableWidgetItem(act["action"]))
            self.activity_table.setItem(row, 2, QTableWidgetItem(act["details"]))

    def _set_active_engagement(self, engagement_id: str) -> None:
        try:
            self.current_engagement = self.engagement_service.get_engagement(engagement_id)
            self.current_client = self.client_service.get_client(self.current_engagement.client_id)
            self.current_firm = self.firm_service.get_firm(self.current_engagement.firm_id)

            self.ctx_title.setText(
                f"{self.current_client.name.upper()}  •  {self.current_engagement.financial_year}"
            )
            self.ctx_sub.setText(
                f"Firm: {self.current_firm.name} | Type: {self.current_engagement.audit_type.value} | Status: {self.current_engagement.status.value}"
            )

            # Highlight workflow stage
            status_map = {
                "Planning": 0,
                "Document Collection": 1,
                "Financial Analysis": 2,
                "Audit Procedures": 3,
                "Review": 4,
                "Completed": 5,
            }
            active_stage_idx = status_map.get(self.current_engagement.status.value, 0)

            for i, w in enumerate(self.stage_widgets):
                if i < active_stage_idx:
                    w.setStyleSheet("""
                        QLabel {
                            background-color: #065f46;
                            color: #a7f3d0;
                            border: 1px solid #10b981;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-weight: 600;
                            font-size: 11px;
                        }
                    """)
                elif i == active_stage_idx:
                    w.setStyleSheet("""
                        QLabel {
                            background-color: #0284c7;
                            color: #ffffff;
                            border: 1px solid #38bdf8;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-weight: 700;
                            font-size: 11px;
                        }
                    """)
                else:
                    w.setStyleSheet("""
                        QLabel {
                            background-color: #121418;
                            color: #64748b;
                            border: 1px solid #2e3440;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-weight: 600;
                            font-size: 11px;
                        }
                    """)
        except Exception:
            self._clear_active_context()

    def _clear_active_context(self) -> None:
        self.current_firm = None
        self.current_client = None
        self.current_engagement = None
        self.ctx_title.setText("NO ACTIVE ENGAGEMENT SELECTED")
        self.ctx_sub.setText("Select or create a firm, client, and engagement to begin audit work.")

    def _on_engagement_combo_changed(self, index: int) -> None:
        eng_id = self.eng_selector_combo.currentData()
        if eng_id:
            self._set_active_engagement(eng_id)
            self.engagement_selected.emit(eng_id)
