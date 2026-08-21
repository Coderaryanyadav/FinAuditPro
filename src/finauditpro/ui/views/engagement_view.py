"""Engagement management view."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import Client, Firm
from finauditpro.ui.dialogs.engagement_dialog import EngagementDialog
from finauditpro.ui.theme import CardWidget


class EngagementView(QWidget):
    """View listing audit engagements with create/edit/activate controls."""

    engagement_changed = Signal(str)  # Emits active engagement id

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

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Audit Engagements")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")

        self.add_btn = QPushButton("+ Create Engagement")
        self.add_btn.clicked.connect(self._create_engagement)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        card = CardWidget()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "Client Name",
                "Financial Year",
                "Audit Type",
                "Workflow Status",
                "Assigned Team",
                "Created Date",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)

        card.content_layout.addWidget(self.table)
        layout.addWidget(card)

    def refresh(self) -> None:
        engagements = self.engagement_service.list_all_engagements()

        self.table.setRowCount(0)
        for row, eng in enumerate(engagements):
            self.table.insertRow(row)
            try:
                client = self.client_service.get_client(eng.client_id)
                client_name = client.name
            except Exception:
                client_name = "Unknown Client"

            item_name = QTableWidgetItem(client_name)
            item_name.setData(Qt.ItemDataRole.UserRole, eng.id)

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(eng.financial_year))
            self.table.setItem(row, 2, QTableWidgetItem(eng.audit_type.value))
            self.table.setItem(row, 3, QTableWidgetItem(eng.status.value))
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(eng.assigned_team)))
            self.table.setItem(row, 5, QTableWidgetItem(eng.created_at.strftime("%Y-%m-%d")))

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
