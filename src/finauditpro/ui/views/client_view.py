"""
Client Directory & Entity Management Workspace View for FinAuditPro.
Enterprise client directory with search, entity filters, and responsive empty states.
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
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import Client, Firm
from finauditpro.ui.dialogs.client_dialog import ClientDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, PageHeader


class ClientView(QWidget):
    """View listing clients for an audit firm with search, filters, and create/edit controls."""

    client_changed = Signal()
    client_selected = Signal(str)

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
        self._all_clients: list[Client] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Clients",
            subtitle="Manage client entities, statutory registrations, and contact relationships.",
            action_text="+ Create New Client",
            action_callback=self._create_client,
        )
        self.add_btn = self.header.action_btn
        layout.addWidget(self.header)

        # 2. Search & Entity Filter Row
        filter_card = CardWidget()
        f_layout = QHBoxLayout()
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(10)

        s_lbl = QLabel("Search:")
        s_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;"
        )
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clients by name, PAN, GSTIN, or industry...")
        self.search_input.setStyleSheet(
            "QLineEdit { border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 7px 12px; font-size: 13px; background: #FFFFFF; color: #0F172A; }"
            "QLineEdit:focus { border-color: #2563EB; }"
        )
        self.search_input.textChanged.connect(self._apply_filters)

        type_lbl = QLabel("Entity:")
        type_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #475569; letter-spacing: 0.3px;"
        )
        self.type_combo = QComboBox()
        self.type_combo.setMinimumWidth(180)
        self.type_combo.addItems(
            [
                "All Entities",
                "Private Limited",
                "Public Limited",
                "LLP",
                "Partnership",
                "Proprietorship",
            ]
        )
        self.type_combo.currentIndexChanged.connect(self._apply_filters)

        f_layout.addWidget(s_lbl)
        f_layout.addWidget(self.search_input, stretch=1)
        f_layout.addSpacing(8)
        f_layout.addWidget(type_lbl)
        f_layout.addWidget(self.type_combo)
        filter_card.content_layout.addLayout(f_layout)
        layout.addWidget(filter_card)

        # 3. Table Card & Empty State
        self.table_card = CardWidget("CLIENT DIRECTORY")
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "CLIENT LEGAL NAME",
                "ENTITY TYPE",
                "PAN",
                "GSTIN",
                "INDUSTRY",
                "CONTACT PERSON",
                "STATUS",
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
        self.table.itemClicked.connect(self._on_table_click)
        self.table.doubleClicked.connect(self._on_double_click)

        self.empty_state = EmptyStateWidget(
            title="No clients registered yet",
            description="Create your first client record to begin an audit engagement and analyze statutory records.",
            action_text="+ Create Client",
            action_callback=self._create_client,
        )

        self.table.setVisible(False)
        self.table_card.content_layout.addWidget(self.table)
        self.table_card.content_layout.addWidget(self.empty_state)
        layout.addWidget(self.table_card)
        layout.addStretch(1)

        self.refresh()


    def set_firm(self, firm: Firm | None) -> None:
        self.current_firm = firm
        if firm:
            self.header.title_lbl.setText(f"Clients — {firm.name}")
            self.header.action_btn.setEnabled(True)
        else:
            self.header.title_lbl.setText("Clients")
            self.header.action_btn.setEnabled(True)
        self.refresh()

    def refresh(self) -> None:
        if not self.current_firm:
            self._all_clients = (
                self.client_service.list_all_clients()
                if hasattr(self.client_service, "list_all_clients")
                else []
            )
        else:
            self._all_clients = self.client_service.list_clients_for_firm(self.current_firm.id)
        self._apply_filters()

    def _apply_filters(self) -> None:
        q = self.search_input.text().strip().lower()
        sel_type = self.type_combo.currentText()

        filtered = []
        for c in self._all_clients:
            if q and (
                q not in c.name.lower()
                and (not c.pan or q not in c.pan.lower())
                and (not c.gstin or q not in c.gstin.lower())
            ):
                continue
            if sel_type != "All Entities":
                ent_val = (
                    c.entity_type.value if hasattr(c.entity_type, "value") else str(c.entity_type)
                )
                if sel_type.lower() not in ent_val.lower():
                    continue
            filtered.append(c)

        if not filtered:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)

        for row, client in enumerate(filtered):
            self.table.insertRow(row)
            item_name = QTableWidgetItem(client.name)
            item_name.setData(Qt.ItemDataRole.UserRole, client.id)
            self.table.setItem(row, 0, item_name)
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    client.entity_type.value
                    if hasattr(client.entity_type, "value")
                    else str(client.entity_type)
                ),
            )
            self.table.setItem(row, 2, QTableWidgetItem(client.pan or "—"))
            self.table.setItem(row, 3, QTableWidgetItem(client.gstin or "—"))
            self.table.setItem(row, 4, QTableWidgetItem(client.industry or "—"))
            self.table.setItem(row, 5, QTableWidgetItem(client.contact_person or "—"))
            self.table.setItem(row, 6, QTableWidgetItem("● Active"))

        self.table.setFixedHeight(max(1, len(filtered)) * 36 + 32)

    def _on_table_click(self, item: QTableWidgetItem) -> None:
        row = item.row()
        name_item = self.table.item(row, 0)
        if name_item:
            client_id = name_item.data(Qt.ItemDataRole.UserRole)
            if client_id:
                self.client_selected.emit(client_id)

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
            if dialog.result_client:
                self.client_selected.emit(dialog.result_client.id)

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
                        if dialog.result_client:
                            self.client_selected.emit(dialog.result_client.id)
                except Exception as ex:
                    QMessageBox.critical(self, "Error", f"Could not load client: {ex}")

