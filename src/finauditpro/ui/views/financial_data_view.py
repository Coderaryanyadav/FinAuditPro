"""
Financial Data Import & Deterministic Analytics Workspace View for FinAuditPro.
Enterprise analytics hub for trial balance imports, exception scanning, and finding promotions.
"""

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

from finauditpro.application.services.financial_service import FinancialService
from finauditpro.domain.entities import Engagement
from finauditpro.domain.financial_entities import FinancialDataset
from finauditpro.ui.dialogs.import_dataset_dialog import ImportDatasetDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, PageHeader, format_inr


class FinancialDataView(QWidget):
    """Primary Financial Data & Deterministic Analytics Workspace view."""

    data_changed = Signal()

    def __init__(
        self,
        client_service: Any = None,
        engagement_service: Any = None,
        financial_service: Any = None,
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

        self.financial_service: FinancialService | None = None
        if isinstance(financial_service, FinancialService):
            self.financial_service = financial_service
        elif hasattr(financial_service, "db_manager"):
            self.financial_service = FinancialService(financial_service.db_manager)


        self.current_engagement: Engagement | None = None
        self.current_dataset: FinancialDataset | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Financial Statements & Analytics",
            subtitle="Import trial balances, journal ledgers, and execute automated anomaly detection.",
            action_text="+ Import Dataset",
            action_callback=self._on_import_clicked,
        )
        self.import_btn = self.header.action_btn
        layout.addWidget(self.header)

        # 2. Dataset Selector Bar
        selector_card = CardWidget()
        sel_layout = QHBoxLayout()
        sel_layout.setContentsMargins(0, 0, 0, 0)
        sel_layout.setSpacing(10)

        sel_lbl = QLabel("Active Dataset:")
        sel_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;"
        )

        self.dataset_combo = QComboBox()
        self.dataset_combo.setMinimumWidth(280)
        self.dataset_combo.addItem("— No Datasets Imported —", None)
        self.dataset_combo.currentIndexChanged.connect(self._on_dataset_changed)

        self.run_analytics_btn = QPushButton("⚡ Run Deterministic Analytics")
        self.run_analytics_btn.setObjectName("primaryButton")
        self.run_analytics_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_analytics_btn.clicked.connect(self._on_run_analytics_clicked)
        self.run_analytics_btn.setEnabled(False)

        sel_layout.addWidget(sel_lbl)
        sel_layout.addWidget(self.dataset_combo, stretch=1)
        sel_layout.addWidget(self.run_analytics_btn)
        selector_card.content_layout.addLayout(sel_layout)
        layout.addWidget(selector_card)

        # 3. Flagged Exceptions Table Card & Empty State
        self.exceptions_card = CardWidget("FLAGGED AUDIT EXCEPTIONS & ANOMALIES")
        self.exceptions_table = QTableWidget()
        self.exceptions_table.setColumnCount(6)
        self.exceptions_table.setHorizontalHeaderLabels(
            [
                "STATUS",
                "ANALYTIC ROUTINE",
                "SEVERITY",
                "EXCEPTION TITLE",
                "COMPUTED EVIDENCE",
                "ACTIONS",
            ]
        )
        self.exceptions_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        for c in [0, 1, 2, 3, 5]:
            self.exceptions_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.exceptions_table.verticalHeader().setVisible(False)
        self.exceptions_table.setAlternatingRowColors(True)

        self.exceptions_empty = EmptyStateWidget(
            title="No audit exceptions flagged",
            description="Run deterministic analytics on the active dataset to scan for round-tripping, unusual weekend postings, and duplicate vouchers.",
            action_text="Run Deterministic Analytics",
            action_callback=self._on_run_analytics_clicked,
        )

        self.exceptions_table.setVisible(False)
        self.exceptions_card.content_layout.addWidget(self.exceptions_table)
        self.exceptions_card.content_layout.addWidget(self.exceptions_empty)
        layout.addWidget(self.exceptions_card)

        # 4. Normalized Records Table Card
        self.records_card = CardWidget("NORMALIZED DATASET ROWS")
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(7)
        self.records_table.setHorizontalHeaderLabels(
            ["ROW #", "DATE", "VOUCHER #", "ACCOUNT NAME", "DEBIT (₹)", "CREDIT (₹)", "NARRATION"]
        )
        self.records_table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Stretch
        )
        for c in range(6):
            self.records_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.setAlternatingRowColors(True)

        self.records_empty = EmptyStateWidget(
            title="No dataset rows loaded",
            description="Import a trial balance or ledger CSV/Excel file to inspect normalized journal records.",
            action_text="+ Import Dataset",
            action_callback=self._on_import_clicked,
        )

        self.records_table.setVisible(False)
        self.records_card.content_layout.addWidget(self.records_table)
        self.records_card.content_layout.addWidget(self.records_empty)
        layout.addWidget(self.records_card)
        layout.addStretch(1)

    def set_engagement(self, engagement: Any) -> None:
        if isinstance(engagement, Engagement):
            self.current_engagement = engagement
            self.header.action_btn.setEnabled(True)
        elif engagement:
            try:
                self.current_engagement = self.engagement_service.get_engagement(str(engagement))
                self.header.action_btn.setEnabled(True)
            except Exception:
                self.current_engagement = None
                self.header.action_btn.setEnabled(False)
        else:
            self.current_engagement = None
            self.header.action_btn.setEnabled(False)
        self.refresh()

    set_active_engagement = set_engagement

    def refresh(self) -> None:
        if not self.current_engagement or not self.financial_service:
            self.dataset_combo.blockSignals(True)
            self.dataset_combo.clear()
            self.dataset_combo.addItem("— No Datasets Imported —", None)
            self.dataset_combo.blockSignals(False)
            self._show_empty_state()
            return

        datasets = self.financial_service.list_datasets_for_engagement(self.current_engagement.id)
        self.dataset_combo.blockSignals(True)
        self.dataset_combo.clear()

        if not datasets:
            self.dataset_combo.addItem("— No Datasets Imported —", None)
            self.current_dataset = None
            self._show_empty_state()
        else:
            for ds in datasets:
                cat_val = ds.dataset_type.value if hasattr(ds.dataset_type, "value") else str(ds.dataset_type)
                self.dataset_combo.addItem(f"{ds.dataset_name} ({ds.valid_rows} rows · {cat_val})", ds.id)
            self.dataset_combo.setCurrentIndex(0)
            self.current_dataset = datasets[0]
            self.run_analytics_btn.setEnabled(True)
            self._load_dataset_rows(self.current_dataset.id)

        self.dataset_combo.blockSignals(False)
        self._load_exceptions()

    def _show_empty_state(self) -> None:
        self.records_table.setVisible(False)
        self.records_empty.setVisible(True)
        self.exceptions_table.setVisible(False)
        self.exceptions_empty.setVisible(True)
        self.run_analytics_btn.setEnabled(False)

    def _on_dataset_changed(self, index: int) -> None:
        ds_id = self.dataset_combo.currentData()
        if ds_id and self.financial_service:
            self._load_dataset_rows(ds_id)
            self._load_exceptions()

    def _load_dataset_rows(self, dataset_id: str) -> None:
        if not self.current_dataset or not self.financial_service:
            return
        records = self.financial_service.list_dataset_rows(dataset_id)
        if not records:
            self.records_table.setVisible(False)
            self.records_empty.setVisible(True)
            return

        self.records_table.setVisible(True)
        self.records_empty.setVisible(False)
        self.records_table.setRowCount(0)

        for row, rec in enumerate(records[:200]):
            self.records_table.insertRow(row)
            self.records_table.setItem(row, 0, QTableWidgetItem(str(rec.get("row_no", row + 1))))
            self.records_table.setItem(row, 1, QTableWidgetItem(str(rec.get("date", "—"))))
            self.records_table.setItem(row, 2, QTableWidgetItem(str(rec.get("voucher_no", "—"))))
            self.records_table.setItem(row, 3, QTableWidgetItem(str(rec.get("account_name", "—"))))
            dr_item = QTableWidgetItem(format_inr(rec.get("debit", 0)))
            dr_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.records_table.setItem(row, 4, dr_item)
            cr_item = QTableWidgetItem(format_inr(rec.get("credit", 0)))
            cr_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.records_table.setItem(row, 5, cr_item)
            self.records_table.setItem(row, 6, QTableWidgetItem(str(rec.get("narration", "—"))))

        self.records_table.setFixedHeight(min(300, max(1, len(records[:200])) * 36 + 32))


    def _load_exceptions(self) -> None:
        if not self.current_dataset or not self.financial_service:
            self.exceptions_table.setVisible(False)
            self.exceptions_empty.setVisible(True)
            return

        exceptions = self.financial_service.list_exceptions_for_dataset(self.current_dataset.id)
        if not exceptions:
            self.exceptions_table.setVisible(False)
            self.exceptions_empty.setVisible(True)
            return

        self.exceptions_table.setVisible(True)
        self.exceptions_empty.setVisible(False)
        self.exceptions_table.setRowCount(0)

        for row, exc in enumerate(exceptions):
            self.exceptions_table.insertRow(row)
            status_val = exc.status.value if hasattr(exc.status, "value") else str(exc.status)

            self.exceptions_table.setItem(row, 0, QTableWidgetItem(f"● {status_val}"))
            self.exceptions_table.setItem(row, 1, QTableWidgetItem(exc.analytic_id))
            self.exceptions_table.setItem(row, 2, QTableWidgetItem(f"● {exc.severity}"))
            rows_str = f" (Rows: {exc.implicated_rows[:5]})" if exc.implicated_rows else ""
            self.exceptions_table.setItem(row, 3, QTableWidgetItem(f"{exc.title}{rows_str}"))
            self.exceptions_table.setItem(row, 4, QTableWidgetItem(exc.computed_evidence))

            action_btn = QPushButton("Accept → Finding")
            action_btn.setEnabled(status_val != "Accepted")
            action_btn.clicked.connect(lambda _, exc_id=exc.id: self._on_promote_finding(exc_id))
            self.exceptions_table.setCellWidget(row, 5, action_btn)

        self.exceptions_table.setFixedHeight(max(1, len(exceptions)) * 36 + 32)

    def _on_import_clicked(self) -> None:
        if not self.current_engagement or not self.financial_service:
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
        if not self.current_dataset or not self.financial_service:
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
        if not self.financial_service:
            return
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
