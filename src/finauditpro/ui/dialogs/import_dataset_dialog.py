"""Import Financial Dataset Wizard Dialog with column auto-detection and remapping."""

from pathlib import Path

from finauditpro.ui.widgets.custom_combo import CustomComboBox
from finauditpro.ui.widgets.custom_combo import CustomComboBox
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
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

from finauditpro.application.services.financial_service import FinancialService, ImportDatasetDTO
from finauditpro.domain.entities import Engagement
from finauditpro.domain.financial_entities import DatasetTypeEnum, FinancialDataset
from finauditpro.ui.theme import CardWidget


class ImportDatasetDialog(QDialog):
    """Wizard dialog for inspecting files, configuring column mappings, and importing financial datasets."""

    def __init__(
        self,
        financial_service: FinancialService,
        engagement: Engagement,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.financial_service = financial_service
        self.engagement = engagement
        self.result_dataset: FinancialDataset | None = None
        self.headers: list[str] = []
        self.detected_mappings: dict[str, str] = {}

        self.setWindowTitle("Import Financial Dataset — Column Mapping Wizard")
        self.resize(750, 600)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Info
        header = QLabel(f"Import Dataset for Engagement FY {self.engagement.financial_year}")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(header)

        # File Selection Card
        file_card = CardWidget("Step 1: Select Financial Data File")
        f_layout = QHBoxLayout()

        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select CSV or Excel file...")
        self.file_path_input.setReadOnly(True)

        browse_btn = QPushButton("Browse File...")
        browse_btn.clicked.connect(self._browse_file)

        f_layout.addWidget(self.file_path_input, stretch=1)
        f_layout.addWidget(browse_btn)

        file_card.content_layout.addLayout(f_layout)
        layout.addWidget(file_card)

        # Metadata Card
        meta_card = CardWidget("Step 2: Dataset Configuration")
        m_layout = QFormLayout()

        self.ds_name_input = QLineEdit()
        self.ds_name_input.setPlaceholderText("e.g. FY 2025-26 General Ledger")

        self.ds_type_combo = CustomComboBox()
        for dt in DatasetTypeEnum:
            self.ds_type_combo.addItem(dt.value, dt)

        m_layout.addRow("Dataset Name *:", self.ds_name_input)
        m_layout.addRow("Dataset Category:", self.ds_type_combo)

        meta_card.content_layout.addLayout(m_layout)
        layout.addWidget(meta_card)

        # Column Mapping Table Card
        mapping_card = CardWidget("Step 3: Column Mapping & Header Verification")
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(
            ["Standard Audit Field", "Source File Column Header"]
        )
        self.mapping_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.mapping_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.mapping_table.verticalHeader().setVisible(False)

        mapping_card.content_layout.addWidget(self.mapping_table)
        layout.addWidget(mapping_card, stretch=1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        self.import_btn = QPushButton("Import Dataset")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._import)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.import_btn)

        layout.addLayout(btn_layout)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Financial Data File",
            "",
            "Financial Data Files (*.csv *.xlsx *.xls);;All Files (*)",
        )

        if file_path:
            self.file_path_input.setText(file_path)
            try:
                self.headers, self.detected_mappings = (
                    self.financial_service.inspect_dataset_headers(file_path)
                )
                filename = Path(file_path).name
                self.ds_name_input.setText(filename)
                self._populate_mapping_table()
                self.import_btn.setEnabled(True)
            except Exception as ex:
                QMessageBox.critical(self, "Inspection Error", f"Could not inspect file: {ex}")

    def _populate_mapping_table(self) -> None:
        if not self.headers:
            return

        std_fields = [
            ("Transaction Date", "date"),
            ("Account Name", "account_name"),
            ("Account Code", "account_code"),
            ("Voucher Type", "voucher_type"),
            ("Voucher / Invoice Number", "voucher_number"),
            ("Debit Amount", "debit"),
            ("Credit Amount", "credit"),
            ("Narration / Description", "narration"),
            ("Opening Debit", "opening_dr"),
            ("Opening Credit", "opening_cr"),
            ("Closing Debit", "closing_dr"),
            ("Closing Credit", "closing_cr"),
            ("Running Balance", "balance"),
            ("Reference / Cheque No", "reference"),
        ]

        self.mapping_table.setRowCount(0)
        self.combo_widgets: dict[str, QComboBox] = {}

        for row, (field_label, field_key) in enumerate(std_fields):
            self.mapping_table.insertRow(row)
            self.mapping_table.setItem(row, 0, QTableWidgetItem(field_label))

            combo = CustomComboBox()
            combo.addItem("-- Not Mapped --", "")
            for h in self.headers:
                combo.addItem(h, h)

            suggested = self.detected_mappings.get(field_key, "")
            idx = combo.findData(suggested)
            if idx >= 0:
                combo.setCurrentIndex(idx)

            self.mapping_table.setCellWidget(row, 1, combo)
            self.combo_widgets[field_key] = combo

    def _import(self) -> None:
        file_path = self.file_path_input.text().strip()
        ds_name = self.ds_name_input.text().strip()

        if not file_path or not ds_name:
            QMessageBox.warning(
                self, "Validation Error", "Please select a file and enter a dataset name."
            )
            return

        column_mappings: dict[str, str] = {}
        for field_key, combo in self.combo_widgets.items():
            selected = combo.currentData()
            if selected:
                column_mappings[field_key] = selected

        dto = ImportDatasetDTO(
            engagement_id=self.engagement.id,
            file_path=file_path,
            dataset_type=self.ds_type_combo.currentData(),
            custom_mappings=column_mappings,
        )

        try:
            self.result_dataset = self.financial_service.import_dataset(dto)
            msg = f"Successfully imported '{self.result_dataset.dataset_name}' ({self.result_dataset.valid_rows} valid rows)."
            if self.result_dataset.error_rows > 0:
                msg += f"\n\nNotice: {self.result_dataset.error_rows} invalid rows were quarantined into the error log."

            QMessageBox.information(self, "Import Successful", msg)
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Import Error", f"Failed to import dataset: {ex}")
