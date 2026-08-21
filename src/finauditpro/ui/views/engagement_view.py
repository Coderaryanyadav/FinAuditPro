"""
Engagement Management Workspace View for FinAuditPro.
Enterprise directory with audit lifecycle filters, status badges, and responsive empty states.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.ui.dialogs.engagement_dialog import EngagementDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, PageHeader


class EngagementView(QWidget):
    """View listing audit engagements with filters, status badges, and create/edit controls."""

    engagement_changed = Signal(str)

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
        self._all_engagements: list[Engagement] = []
        self._client_map: dict[str, str] = {}

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Audit Engagements",
            subtitle="Manage audit engagements, financial years, teams, and workflow status.",
            action_text="+ Create Engagement",
            action_callback=self._create_engagement,
        )
        self.add_btn = self.header.action_btn
        layout.addWidget(self.header)

        # 2. Search & Filter Row
        filter_card = CardWidget()
        f_layout = QHBoxLayout()
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(10)

        s_lbl = QLabel("Search:")
        s_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;"
        )
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search engagements by client name, FY, or audit type..."
        )
        self.search_input.setStyleSheet(
            "QLineEdit { border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 10px; font-size: 12px; background: #FFFFFF; }"
            "QLineEdit:focus { border-color: #2563EB; }"
        )
        self.search_input.textChanged.connect(self._apply_filters)

        type_lbl = QLabel("Type:")
        type_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;"
        )
        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["All Types", "Statutory Audit", "Tax Audit", "Internal Audit", "GST Audit"]
        )
        self.type_combo.currentIndexChanged.connect(self._apply_filters)

        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;"
        )
        self.status_combo = QComboBox()
        self.status_combo.addItems(
            ["All Statuses", "Planning", "In Progress", "Review", "Completed", "Archived"]
        )
        self.status_combo.currentIndexChanged.connect(self._apply_filters)

        f_layout.addWidget(s_lbl)
        f_layout.addWidget(self.search_input, stretch=1)
        f_layout.addWidget(type_lbl)
        f_layout.addWidget(self.type_combo)
        f_layout.addWidget(status_lbl)
        f_layout.addWidget(self.status_combo)
        filter_card.content_layout.addLayout(f_layout)
        layout.addWidget(filter_card)

        # 3. Table Card & Empty State
        self.table_card = CardWidget("AUDIT ENGAGEMENTS")
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "CLIENT",
                "FINANCIAL YEAR",
                "AUDIT TYPE",
                "STATUS",
                "ASSIGNED TEAM",
                "CREATED DATE",
                "ACTION",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 7):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._on_double_click)

        self.empty_state = EmptyStateWidget(
            title="No audit engagements found",
            description="Create an engagement to begin the audit lifecycle, materiality assessment, risk register, and working papers.",
            action_text="+ Create Engagement",
            action_callback=self._create_engagement,
        )

        self.table_card.content_layout.addWidget(self.table)
        self.table_card.content_layout.addWidget(self.empty_state)
        layout.addWidget(self.table_card)
        layout.addStretch(1)

        self.refresh()

    def refresh(self) -> None:
        self._all_engagements = self.engagement_service.list_all_engagements()
        clients = (
            self.client_service.list_all_clients()
            if hasattr(self.client_service, "list_all_clients")
            else []
        )
        self._client_map = {c.id: c.name for c in clients}
        self._apply_filters()

    def _apply_filters(self) -> None:
        q = self.search_input.text().strip().lower()
        sel_type = self.type_combo.currentText()
        sel_status = self.status_combo.currentText()

        filtered = []
        for eng in self._all_engagements:
            c_name = self._client_map.get(eng.client_id, "Unknown Client")
            audit_t = (
                eng.audit_type.value if hasattr(eng.audit_type, "value") else str(eng.audit_type)
            )
            status_v = eng.status.value if hasattr(eng.status, "value") else str(eng.status)

            if q and (
                q not in c_name.lower()
                and q not in eng.financial_year.lower()
                and q not in audit_t.lower()
            ):
                continue
            if sel_type != "All Types" and sel_type.lower() not in audit_t.lower():
                continue
            if sel_status != "All Statuses" and sel_status.lower() not in status_v.lower():
                continue
            filtered.append(eng)

        if not filtered:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)

        for row, eng in enumerate(filtered):
            self.table.insertRow(row)
            c_name = self._client_map.get(eng.client_id, "Unknown Client")
            audit_t = (
                eng.audit_type.value if hasattr(eng.audit_type, "value") else str(eng.audit_type)
            )
            status_val = eng.status.value if hasattr(eng.status, "value") else str(eng.status)

            item_name = QTableWidgetItem(c_name)
            item_name.setData(Qt.ItemDataRole.UserRole, eng.id)

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(f"FY {eng.financial_year}"))
            self.table.setItem(row, 2, QTableWidgetItem(audit_t))
            self.table.setItem(row, 3, QTableWidgetItem(f"● {status_val}"))
            self.table.setItem(
                row, 4, QTableWidgetItem(", ".join(eng.assigned_team) or "Unassigned")
            )
            self.table.setItem(row, 5, QTableWidgetItem(eng.created_at.strftime("%Y-%m-%d")))
            self.table.setItem(row, 6, QTableWidgetItem("Open →"))

        self.table.setFixedHeight(max(1, len(filtered)) * 36 + 32)

    def _create_engagement(self) -> None:
        firms = self.firm_service.list_firms()
        if not firms:
            QMessageBox.warning(self, "No Firm", "Please create an Audit Firm first.")
            return
        firm = firms[0]

        clients = self.client_service.list_clients_for_firm(firm.id)
        if not clients:
            QMessageBox.warning(
                self, "No Client", "Please create a Client first before adding an Engagement."
            )
            return
        client = clients[0]

        dialog = EngagementDialog(self.engagement_service, firm=firm, client=client, parent=self)
        if dialog.exec() == EngagementDialog.DialogCode.Accepted:
            self.refresh()
            if dialog.result_engagement:
                self.engagement_changed.emit(dialog.result_engagement.id)

    def _on_double_click(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item is not None:
                eng_id = item.data(Qt.ItemDataRole.UserRole)
                try:
                    eng = self.engagement_service.get_engagement(eng_id)
                    client = self.client_service.get_client(eng.client_id)
                    firm = self.firm_service.get_firm(eng.firm_id)
                    dialog = EngagementDialog(
                        self.engagement_service,
                        firm=firm,
                        client=client,
                        engagement=eng,
                        parent=self,
                    )
                    if dialog.exec() == EngagementDialog.DialogCode.Accepted:
                        self.refresh()
                        self.engagement_changed.emit(eng.id)
                except Exception as ex:
                    QMessageBox.critical(self, "Error", f"Could not load engagement: {ex}")
