"""Financial Data Import & Deterministic Analytics Workspace View."""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
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
from finauditpro.application.services.financial_service import FinancialService
from finauditpro.domain.entities import Engagement
from finauditpro.domain.financial_entities import (
    FinancialDataset,
)
from finauditpro.ui.dialogs.import_dataset_dialog import ImportDatasetDialog
from finauditpro.ui.theme import CardWidget


class FinancialDataView(QWidget):
    """Primary Financial Data & Deterministic Analytics Workspace view."""

    data_changed = Signal()

    def __init__(
        self,
        client_service: ClientService,
        engagement_service: EngagementService,
        financial_service: FinancialService | Any = None,
        financial_analytics_service: Any = None,
        parent: QWidget | None = None,
    ) -> None:
        if isinstance(financial_analytics_service, QWidget):
            parent_widget = financial_analytics_service
        elif isinstance(parent, QWidget):
            parent_widget = parent
        else:
            parent_widget = None

        super().__init__(parent_widget)
        self.client_service = client_service
        self.engagement_service = engagement_service

        if isinstance(financial_service, FinancialService):
            self.financial_service = financial_service
        elif hasattr(financial_service, "db_manager"):
            self.financial_service = FinancialService(financial_service.db_manager)
        else:
            self.financial_service = None  # type: ignore

        self.current_engagement: Engagement | None = None
        self.current_dataset: FinancialDataset | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Row
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Financial Data & Deterministic Analytics Workspace")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")

        self.import_btn = QPushButton("+ Import Financial Dataset")
        self.import_btn.clicked.connect(self._on_import_clicked)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.import_btn)

        layout.addLayout(header_layout)

        # Dataset Selector Bar
        selector_card = CardWidget()
        sel_layout = QHBoxLayout()

        sel_lbl = QLabel("Active Dataset:")
        sel_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #94a3b8;")

        self.dataset_combo = QComboBox()
        self.dataset_combo.setMinimumWidth(280)
        self.dataset_combo.currentIndexChanged.connect(self._on_dataset_changed)

        self.run_analytics_btn = QPushButton("Run Deterministic Analytics")
        self.run_analytics_btn.clicked.connect(self._on_run_analytics_clicked)

        sel_layout.addWidget(sel_lbl)
        sel_layout.addWidget(self.dataset_combo, stretch=1)
        sel_layout.addWidget(self.run_analytics_btn)

        selector_card.content_layout.addLayout(sel_layout)
        layout.addWidget(selector_card)

        # Flagged Exceptions Table Card
        exceptions_card = CardWidget("Flagged Audit Exceptions & Transaction Indicators")
        self.exceptions_table = QTableWidget()
        self.exceptions_table.setColumnCount(6)
        self.exceptions_table.setHorizontalHeaderLabels(
            [
                "Status",
                "Analytic Routine",
                "Severity",
                "Title / Implicated Rows",
                "Computed Evidence",
                "Actions",
            ]
        )
        self.exceptions_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.exceptions_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.exceptions_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.exceptions_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.exceptions_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.exceptions_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.exceptions_table.verticalHeader().setVisible(False)
        self.exceptions_table.setMinimumHeight(200)

        exceptions_card.content_layout.addWidget(self.exceptions_table)
        layout.addWidget(exceptions_card)

        # Financial Records Table Card
        records_card = CardWidget("Normalized Dataset Rows Inspector")
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(7)
        self.records_table.setHorizontalHeaderLabels(
            [
                "Row #",
                "Date",
                "Voucher #",
                "Account Name",
                "Debit (INR)",
                "Credit (INR)",
                "Narration",
            ]
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Stretch
        )
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.setMinimumHeight(200)

        records_card.content_layout.addWidget(self.records_table)
        layout.addWidget(records_card)

    def set_engagement(self, engagement_id: str | None) -> None:
        if engagement_id:
            try:
                self.current_engagement = self.engagement_service.get_engagement(engagement_id)
                self.import_btn.setEnabled(True)
            except Exception:
                self.current_engagement = None
                self.import_btn.setEnabled(False)
        else:
            self.current_engagement = None
            self.import_btn.setEnabled(False)

        self.refresh()

    def refresh(self) -> None:
        if not self.current_engagement:
            self.dataset_combo.clear()
            self.records_table.setRowCount(0)
            self.exceptions_table.setRowCount(0)
            self.run_analytics_btn.setEnabled(False)
            return

        datasets = self.financial_service.list_datasets_for_engagement(self.current_engagement.id)
        self.dataset_combo.blockSignals(True)
        self.dataset_combo.clear()

        if not datasets:
            self.dataset_combo.addItem("-- No Datasets Imported --", None)
            self.current_dataset = None
            self.records_table.setRowCount(0)
            self.exceptions_table.setRowCount(0)
            self.run_analytics_btn.setEnabled(False)
        else:
            for ds in datasets:
                cat_val = (
                    ds.dataset_type.value
                    if hasattr(ds.dataset_type, "value")
                    else str(ds.dataset_type)
                )
                self.dataset_combo.addItem(
                    f"{ds.dataset_name} ({ds.valid_rows} rows, {cat_val})", ds.id
                )

            self.dataset_combo.setCurrentIndex(0)
            self.current_dataset = datasets[0]
            self.run_analytics_btn.setEnabled(True)
            self._load_dataset_rows(self.current_dataset.id)

        self.dataset_combo.blockSignals(False)
        self._load_exceptions()

    def _on_dataset_changed(self, index: int) -> None:
        ds_id = self.dataset_combo.currentData()
        if ds_id:
            self._load_dataset_rows(ds_id)
            self._load_exceptions()

    def _load_dataset_rows(self, dataset_id: str) -> None:
        if not self.current_dataset:
            return
        records = self.financial_service.list_dataset_rows(dataset_id)
        self.records_table.setRowCount(0)

        for row, rec in enumerate(records[:500]):
            self.records_table.insertRow(row)
            self.records_table.setItem(row, 0, QTableWidgetItem(str(rec.get("row_no", row + 1))))
            self.records_table.setItem(row, 1, QTableWidgetItem(str(rec.get("date", "-"))))
            self.records_table.setItem(row, 2, QTableWidgetItem(str(rec.get("voucher_no", "-"))))
            self.records_table.setItem(row, 3, QTableWidgetItem(str(rec.get("account_name", "-"))))
            self.records_table.setItem(row, 4, QTableWidgetItem(str(rec.get("debit", "-"))))
            self.records_table.setItem(row, 5, QTableWidgetItem(str(rec.get("credit", "-"))))
            self.records_table.setItem(row, 6, QTableWidgetItem(str(rec.get("narration", "-"))))

    def _load_exceptions(self) -> None:
        if not self.current_dataset:
            self.exceptions_table.setRowCount(0)
            return

        exceptions = self.financial_service.list_exceptions_for_dataset(self.current_dataset.id)
        self.exceptions_table.setRowCount(0)

        for row, exc in enumerate(exceptions):
            self.exceptions_table.insertRow(row)

            status_val = exc.status.value if hasattr(exc.status, "value") else str(exc.status)
            status_item = QTableWidgetItem(status_val)
            if status_val == "Accepted":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status_val == "Open":
                status_item.setForeground(Qt.GlobalColor.yellow)

            self.exceptions_table.setItem(row, 0, status_item)
            self.exceptions_table.setItem(row, 1, QTableWidgetItem(exc.analytic_id))

            sev_item = QTableWidgetItem(exc.severity)
            if exc.severity == "High":
                sev_item.setForeground(Qt.GlobalColor.red)
            elif exc.severity == "Medium":
                sev_item.setForeground(Qt.GlobalColor.yellow)
            self.exceptions_table.setItem(row, 2, sev_item)

            rows_str = f" (Rows: {exc.implicated_rows[:5]})" if exc.implicated_rows else ""
            self.exceptions_table.setItem(row, 3, QTableWidgetItem(f"{exc.title}{rows_str}"))
            self.exceptions_table.setItem(row, 4, QTableWidgetItem(exc.computed_evidence))

            action_btn = QPushButton("Accept → Finding")
            action_btn.setObjectName("SecondaryButton")
            action_btn.setEnabled(status_val != "Accepted")
            action_btn.clicked.connect(lambda _, exc_id=exc.id: self._on_promote_finding(exc_id))

            self.exceptions_table.setCellWidget(row, 5, action_btn)

    def _on_import_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        dialog = ImportDatasetDialog(
            self.financial_service, engagement=self.current_engagement, parent=self
        )
        if dialog.exec() == ImportDatasetDialog.DialogCode.Accepted:
            self.refresh()
            self.data_changed.emit()

    def _on_run_analytics_clicked(self) -> None:
        if not self.current_dataset:
            QMessageBox.warning(self, "No Dataset", "Please select an active dataset to analyze.")
            return

        try:
            exceptions = self.financial_service.run_deterministic_analytics(self.current_dataset.id)
            QMessageBox.information(
                self,
                "Analytics Complete",
                f"Ran deterministic analytics on '{self.current_dataset.dataset_name}'. Flagged {len(exceptions)} exceptions.",
            )
            self._load_exceptions()
            self.data_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Analytics Error", f"Failed to run analytics: {ex}")

    def _on_promote_finding(self, exception_id: str) -> None:
        try:
            finding = self.financial_service.promote_exception_to_finding(exception_id)
            QMessageBox.information(
                self,
                "Finding Created",
                f"Successfully promoted exception to formal audit finding:\n'{finding.title}'",
            )
            self._load_exceptions()
            self.data_changed.emit()
        except Exception as ex:
            QMessageBox.critical(
                self, "Promotion Error", f"Could not promote exception to finding: {ex}"
            )
