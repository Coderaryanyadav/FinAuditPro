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
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import Firm
from finauditpro.ui.dialogs.firm_dialog import FirmDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, PageHeader


class FirmView(QWidget):
    """View listing audit firms with search, filters, and create/edit controls."""

    firm_changed = Signal()
    firm_selected = Signal(str)

    def __init__(self, firm_service: FirmService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self._all_firms: list[Firm] = []
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
        s_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search firms by name, registration (FRN), or PAN...")
        self.search_input.setStyleSheet(
            "QLineEdit { border: 1px solid #CBD5E1; border-radius: 6px; padding: 7px 12px; font-size: 13px; background: #FFFFFF; color: #0F172A; }"
            "QLineEdit:focus { border-color: #2563EB; }"
        )
        self.search_input.textChanged.connect(self._filter_firms)

        clear_btn = QPushButton("Clear")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(
            "QPushButton { background-color: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 14px; font-weight: 500; } QPushButton:hover { background-color: #F1F5F9; color: #1E293B; border-color: #94A3B8; }"
        )
        clear_btn.clicked.connect(self.search_input.clear)

        f_layout.addWidget(s_lbl)
        f_layout.addWidget(self.search_input, stretch=1)
        f_layout.addWidget(clear_btn)
        filter_card.content_layout.addLayout(f_layout)
        layout.addWidget(filter_card)

        # 3. Table Card & Empty State
        self.table_card = CardWidget("REGISTERED AUDIT FIRMS")
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "FIRM NAME",
                "REGISTRATION NO. (FRN)",
                "PAN",
                "GSTIN",
                "PHONE",
                "EMAIL",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self._on_table_click)
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

    def _on_table_click(self, item: QTableWidgetItem) -> None:
        row = item.row()
        name_item = self.table.item(row, 0)
        if name_item:
            firm_id = name_item.data(Qt.ItemDataRole.UserRole)
            if firm_id:
                self.firm_selected.emit(firm_id)

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
            if dialog.result_firm:
                self.firm_selected.emit(dialog.result_firm.id)

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
                        if dialog.result_firm:
                            self.firm_selected.emit(dialog.result_firm.id)
                except Exception as ex:
                    QMessageBox.critical(self, "Error", f"Could not load firm: {ex}")
