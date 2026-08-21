"""Client management view."""

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
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import Firm
from finauditpro.ui.dialogs.client_dialog import ClientDialog
from finauditpro.ui.theme import CardWidget


class ClientView(QWidget):
    """View listing clients for an audit firm with create/edit controls."""

    client_changed = Signal()

    def __init__(
        self,
        firm_service: FirmService,
        client_service: ClientService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self.client_service = client_service
        self.current_firm: Firm | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("Client Directory")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")

        self.add_btn = QPushButton("+ Create New Client")
        self.add_btn.clicked.connect(self._create_client)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        card = CardWidget()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Client Legal Name", "Entity Type", "PAN", "GSTIN", "Industry", "Contact Person"]
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

    def set_firm(self, firm: Firm | None) -> None:
        self.current_firm = firm
        if firm:
            self.title_label.setText(f"Client Directory ({firm.name})")
            self.add_btn.setEnabled(True)
        else:
            self.title_label.setText("Client Directory (Select a Firm First)")
            self.add_btn.setEnabled(False)
        self.refresh()

    def refresh(self) -> None:
        if not self.current_firm:
            clients = self.client_service.list_all_clients()
        else:
            clients = self.client_service.list_clients_for_firm(self.current_firm.id)

        self.table.setRowCount(0)
        for row, client in enumerate(clients):
            self.table.insertRow(row)
            item_name = QTableWidgetItem(client.name)
            item_name.setData(Qt.ItemDataRole.UserRole, client.id)
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(client.entity_type.value))
            self.table.setItem(row, 2, QTableWidgetItem(client.pan or "-"))
            self.table.setItem(row, 3, QTableWidgetItem(client.gstin or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(client.industry or "-"))
            self.table.setItem(row, 5, QTableWidgetItem(client.contact_person or "-"))

    def _create_client(self) -> None:
        if not self.current_firm:
            firms = self.firm_service.list_firms()
            if not firms:
                QMessageBox.warning(
                    self, "No Firm", "Please create an Audit Firm first before creating a client."
                )
                return
            self.current_firm = firms[0]

        dialog = ClientDialog(self.client_service, firm=self.current_firm, parent=self)
        if dialog.exec() == ClientDialog.DialogCode.Accepted:
            self.refresh()
            self.client_changed.emit()

    def _on_double_click(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item is not None:
                client_id = item.data(Qt.ItemDataRole.UserRole)
                try:
                    client = self.client_service.get_client(client_id)
                    firm = self.firm_service.get_firm(client.firm_id)
                    dialog = ClientDialog(
                        self.client_service, firm=firm, client=client, parent=self
                    )
                    if dialog.exec() == ClientDialog.DialogCode.Accepted:
                        self.refresh()
                        self.client_changed.emit()
                except Exception as ex:
                    QMessageBox.critical(self, "Error", f"Could not load client: {ex}")
