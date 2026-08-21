"""Firm management view."""

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

from finauditpro.application.services.firm_service import FirmService
from finauditpro.ui.dialogs.firm_dialog import FirmDialog
from finauditpro.ui.theme import CardWidget


class FirmView(QWidget):
    """View listing audit firms with create/edit controls."""

    firm_changed = Signal()

    def __init__(self, firm_service: FirmService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("Audit Firm Management")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")

        add_btn = QPushButton("+ Create Audit Firm")
        add_btn.clicked.connect(self._create_firm)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        card = CardWidget()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Firm Name", "FRN / Reg No", "PAN", "GSTIN", "Phone", "Email"]
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
        firms = self.firm_service.list_firms()
        self.table.setRowCount(0)
        for row, firm in enumerate(firms):
            self.table.insertRow(row)
            item_name = QTableWidgetItem(firm.name)
            item_name.setData(Qt.ItemDataRole.UserRole, firm.id)
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(firm.registration_number or "-"))
            self.table.setItem(row, 2, QTableWidgetItem(firm.pan or "-"))
            self.table.setItem(row, 3, QTableWidgetItem(firm.gstin or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(firm.phone or "-"))
            self.table.setItem(row, 5, QTableWidgetItem(firm.email or "-"))

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
