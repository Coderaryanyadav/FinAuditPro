"""
Audit Firm Management Workspace View for FinAuditPro.
Enterprise directory with realtime search, clean empty state, and responsive tables.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
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

from finauditpro.application.services.firm_service import FirmService
from finauditpro.ui.dialogs.firm_dialog import FirmDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, PageHeader


class FirmView(QWidget):
    """View listing audit firms with search, filters, and create/edit controls."""

    firm_changed = Signal()

    def __init__(self, firm_service: FirmService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self._all_firms = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Audit Firms",
            subtitle="Manage audit firms, registration numbers (FRN), and practice-level settings.",
            action_text="+ Create Audit Firm",
            action_callback=self._create_firm,
        )
        self.add_btn = self.header.action_btn
        layout.addWidget(self.header)

        # 2. Search Filter Row
        filter_card = CardWidget()
        f_layout = QHBoxLayout()
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(10)

        s_lbl = QLabel("Search:")
        s_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;"
        )
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by firm name, FRN, PAN, or GSTIN...")
        self.search_input.setStyleSheet(
            "QLineEdit { border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 10px; font-size: 12px; background: #FFFFFF; }"
            "QLineEdit:focus { border-color: #2563EB; }"
        )
        self.search_input.textChanged.connect(self._filter_firms)

        f_layout.addWidget(s_lbl)
        f_layout.addWidget(self.search_input, stretch=1)
        filter_card.content_layout.addLayout(f_layout)
        layout.addWidget(filter_card)

        # 3. Table Card & Empty State
        self.table_card = CardWidget("REGISTERED AUDIT FIRMS")
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["FIRM NAME", "FRN / REG NO", "PAN", "GSTIN", "PHONE", "EMAIL"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._on_double_click)

        self.empty_state = EmptyStateWidget(
            title="No audit firms registered yet",
            description="Create your first audit firm profile to begin managing clients, statutory engagements, and working papers.",
            action_text="+ Create Audit Firm",
            action_callback=self._create_firm,
        )

        self.table_card.content_layout.addWidget(self.table)
        self.table_card.content_layout.addWidget(self.empty_state)
        layout.addWidget(self.table_card)
        layout.addStretch(1)

        self.refresh()

    def refresh(self) -> None:
        self._all_firms = self.firm_service.list_firms()
        self._filter_firms(self.search_input.text())

    def _filter_firms(self, query: str = "") -> None:
        q = query.strip().lower()
        filtered = [
            f
            for f in self._all_firms
            if not q
            or q in f.name.lower()
            or (f.registration_number and q in f.registration_number.lower())
            or (f.pan and q in f.pan.lower())
        ]

        if not filtered:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)

        for row, firm in enumerate(filtered):
            self.table.insertRow(row)
            item_name = QTableWidgetItem(firm.name)
            item_name.setData(Qt.ItemDataRole.UserRole, firm.id)
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(firm.registration_number or "—"))
            self.table.setItem(row, 2, QTableWidgetItem(firm.pan or "—"))
            self.table.setItem(row, 3, QTableWidgetItem(firm.gstin or "—"))
            self.table.setItem(row, 4, QTableWidgetItem(firm.phone or "—"))
            self.table.setItem(row, 5, QTableWidgetItem(firm.email or "—"))

        self.table.setFixedHeight(max(1, len(filtered)) * 36 + 32)

    def _create_firm(self) -> None:
        dialog = FirmDialog(self.firm_service, parent=self)
        if dialog.exec() == FirmDialog.DialogCode.Accepted:
            self.refresh()
            self.firm_changed.emit()

    def _on_double_click(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item is not None:
                firm_id = item.data(Qt.ItemDataRole.UserRole)
                try:
                    firm = self.firm_service.get_firm(firm_id)
                    dialog = FirmDialog(self.firm_service, firm=firm, parent=self)
                    if dialog.exec() == FirmDialog.DialogCode.Accepted:
                        self.refresh()
                        self.firm_changed.emit()
                except Exception as ex:
                    QMessageBox.critical(self, "Error", f"Could not load firm: {ex}")
