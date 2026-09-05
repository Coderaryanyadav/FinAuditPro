"""Interactive Modal Dialog for creating and editing Audit Adjusting Journal Entries (AJE)."""

from datetime import date
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
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

from finauditpro.application.audit_adjustment_dtos import (
    CreateAJEDTO,
    CreateAJELineDTO,
    SubmitAJEDTO,
    UpdateAJEDTO,
)
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.domain.audit_adjustment_entities import AJETypeEnum, AuditJournalEntry


def _parse_paise(val: Any) -> int:
    if not val:
        return 0
    clean = str(val).replace("₹", "").replace(",", "").replace(" ", "").strip()
    if not clean or clean in ("-", "—", "NaN", "null"):
        return 0
    try:
        return int(round(float(clean) * 100))
    except (ValueError, TypeError):
        return 0


class CreateAJEDialog(QDialog):
    """CA-friendly interactive dialog to record balanced multi-line Audit Adjusting Journal Entries."""

    def __init__(
        self,
        adjustment_service: AuditAdjustmentService,
        engagement_id: str,
        existing_entry: AuditJournalEntry | None = None,
        available_accounts: list[dict[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.adjustment_service = adjustment_service
        self.engagement_id = engagement_id
        self.existing_entry = existing_entry
        self.available_accounts = available_accounts or []
        self.saved_entry: AuditJournalEntry | None = None

        self.setWindowTitle(
            f"{'Edit' if existing_entry else 'New'} Audit Adjustment Entry (AJE)"
        )
        self.resize(920, 580)
        self.setModal(True)

        self._init_ui()
        if existing_entry:
            self._load_existing_entry(existing_entry)
        else:
            self._add_default_blank_lines()
        self._recalculate_totals()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        meta_frame = QFrame()
        meta_frame.setStyleSheet("background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px;")
        meta_layout = QVBoxLayout(meta_frame)
        meta_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("AJE #:"))
        self.aje_num_input = QLineEdit()
        if not self.existing_entry:
            count = len(self.adjustment_service.list_adjustments(self.engagement_id))
            self.aje_num_input.setText(f"AJE-{count + 1:03d}")
        else:
            self.aje_num_input.setText(self.existing_entry.aje_number)
            self.aje_num_input.setReadOnly(True)
        row1.addWidget(self.aje_num_input, 1)

        row1.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit(date.today())
        self.date_input.setCalendarPopup(True)
        row1.addWidget(self.date_input, 1)

        row1.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Management Accepted", AJETypeEnum.MANAGEMENT_ACCEPTED)
        self.type_combo.addItem("Uncorrected / Passed", AJETypeEnum.UNCORRECTED_PASSED)
        row1.addWidget(self.type_combo, 1)

        row1.addWidget(QLabel("WP Ref:"))
        self.wp_ref_input = QLineEdit()
        self.wp_ref_input.setPlaceholderText("WP-C2")
        row1.addWidget(self.wp_ref_input, 1)
        meta_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        row2.addWidget(self.title_input, 2)
        row2.addWidget(QLabel("Reason:"))
        self.reason_input = QLineEdit()
        row2.addWidget(self.reason_input, 2)
        meta_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Narration:"))
        self.narration_input = QLineEdit()
        row3.addWidget(self.narration_input, 1)
        meta_layout.addLayout(row3)
        layout.addWidget(meta_frame)

        tbl_bar = QHBoxLayout()
        tbl_bar.addWidget(QLabel("JOURNAL LINES (DOUBLE-ENTRY)"))
        tbl_bar.addStretch()
        self.add_line_btn = QPushButton("+ Add Line")
        self.add_line_btn.clicked.connect(self._on_add_line_clicked)
        tbl_bar.addWidget(self.add_line_btn)
        self.del_line_btn = QPushButton("Remove Line")
        self.del_line_btn.clicked.connect(self._on_remove_line_clicked)
        tbl_bar.addWidget(self.del_line_btn)
        layout.addLayout(tbl_bar)

        self.lines_table = QTableWidget(0, 5)
        self.lines_table.setHorizontalHeaderLabels(["CODE", "ACCOUNT NAME", "DEBIT (₹)", "CREDIT (₹)", "NARRATION"])
        self.lines_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.lines_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for c in (0, 2, 3):
            self.lines_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.itemChanged.connect(self._on_cell_changed)
        layout.addWidget(self.lines_table, 1)

        self.balance_bar = QFrame()
        self.balance_bar.setStyleSheet("background: #FEF2F2; border: 1px solid #F87171; border-radius: 6px; padding: 6px;")
        b_lay = QHBoxLayout(self.balance_bar)
        self.total_dr_lbl = QLabel("Total Debits: ₹0.00")
        self.total_cr_lbl = QLabel("Total Credits: ₹0.00")
        self.imbalance_lbl = QLabel("Imbalance: ₹0.00")
        b_lay.addWidget(self.total_dr_lbl)
        b_lay.addSpacing(16)
        b_lay.addWidget(self.total_cr_lbl)
        b_lay.addSpacing(16)
        b_lay.addWidget(self.imbalance_lbl)
        b_lay.addStretch()
        layout.addWidget(self.balance_bar)

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addWidget(cancel_btn)
        self.save_draft_btn = QPushButton("Save Draft AJE")
        self.save_draft_btn.clicked.connect(self._on_save_clicked)
        btn_bar.addWidget(self.save_draft_btn)
        self.submit_btn = QPushButton("Save & Submit")
        self.submit_btn.setObjectName("primaryButton")
        self.submit_btn.clicked.connect(self._on_submit_clicked)
        btn_bar.addWidget(self.submit_btn)
        layout.addLayout(btn_bar)

    def _add_default_blank_lines(self) -> None:
        self.lines_table.blockSignals(True)
        self.lines_table.setRowCount(2)
        for r in range(2):
            for c in range(5):
                self.lines_table.setItem(r, c, QTableWidgetItem("0.00" if c in (2, 3) else ""))
        self.lines_table.blockSignals(False)

    def _load_existing_entry(self, entry: AuditJournalEntry) -> None:
        self.aje_num_input.setText(entry.aje_number)
        self.title_input.setText(entry.title)
        self.narration_input.setText(entry.narration)
        self.reason_input.setText(entry.reason)
        self.wp_ref_input.setText(entry.working_paper_ref or "")
        idx = self.type_combo.findData(entry.aje_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.lines_table.blockSignals(True)
        self.lines_table.setRowCount(len(entry.lines))
        for r, line in enumerate(entry.lines):
            self.lines_table.setItem(r, 0, QTableWidgetItem(line.account_code))
            self.lines_table.setItem(r, 1, QTableWidgetItem(line.account_name))
            self.lines_table.setItem(r, 2, QTableWidgetItem(f"{line.debit_paise / 100:,.2f}"))
            self.lines_table.setItem(r, 3, QTableWidgetItem(f"{line.credit_paise / 100:,.2f}"))
            self.lines_table.setItem(r, 4, QTableWidgetItem(line.narration or ""))
        self.lines_table.blockSignals(False)

    def _on_add_line_clicked(self) -> None:
        self.lines_table.blockSignals(True)
        r = self.lines_table.rowCount()
        self.lines_table.insertRow(r)
        for c in range(5):
            self.lines_table.setItem(r, c, QTableWidgetItem("0.00" if c in (2, 3) else ""))
        self.lines_table.blockSignals(False)
        self._recalculate_totals()

    def _on_remove_line_clicked(self) -> None:
        sel = self.lines_table.currentRow()
        if sel >= 0:
            self.lines_table.removeRow(sel)
            self._recalculate_totals()

    def _on_cell_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == 0:
            code = item.text().strip()
            for acc in self.available_accounts:
                if acc.get("account_code") == code:
                    self.lines_table.blockSignals(True)
                    self.lines_table.setItem(item.row(), 1, QTableWidgetItem(acc.get("account_name", "")))
                    self.lines_table.blockSignals(False)
                    break
        elif item.column() in (2, 3):
            self._recalculate_totals()

    def _get_table_totals_paise(self) -> tuple[int, int]:
        tot_dr = sum(max(0, _parse_paise(self.lines_table.item(r, 2).text() if self.lines_table.item(r, 2) else 0)) for r in range(self.lines_table.rowCount()))
        tot_cr = sum(max(0, _parse_paise(self.lines_table.item(r, 3).text() if self.lines_table.item(r, 3) else 0)) for r in range(self.lines_table.rowCount()))
        return tot_dr, tot_cr

    def _recalculate_totals(self) -> None:
        tot_dr, tot_cr = self._get_table_totals_paise()
        diff = abs(tot_dr - tot_cr)
        is_balanced = (tot_dr == tot_cr) and (tot_dr > 0)
        self.total_dr_lbl.setText(f"Total Debits: ₹{tot_dr / 100:,.2f}")
        self.total_cr_lbl.setText(f"Total Credits: ₹{tot_cr / 100:,.2f}")
        if is_balanced:
            self.balance_bar.setStyleSheet("background: #F0FDF4; border: 1px solid #4ADE80; border-radius: 6px; padding: 6px;")
            self.imbalance_lbl.setText("Imbalance: ₹0.00 (BALANCED)")
            self.imbalance_lbl.setStyleSheet("color: #16A34A; font-weight: 700;")
        else:
            self.balance_bar.setStyleSheet("background: #FEF2F2; border: 1px solid #F87171; border-radius: 6px; padding: 6px;")
            self.imbalance_lbl.setText(f"Imbalance: ₹{diff / 100:,.2f} ({'ZERO' if tot_dr == 0 else 'UNBALANCED'})")
            self.imbalance_lbl.setStyleSheet("color: #DC2626; font-weight: 700;")
        self.save_draft_btn.setEnabled(is_balanced)
        self.submit_btn.setEnabled(is_balanced)

    def _collect_lines(self) -> list[CreateAJELineDTO]:
        lines: list[CreateAJELineDTO] = []
        for r in range(self.lines_table.rowCount()):
            code = (self.lines_table.item(r, 0).text() if self.lines_table.item(r, 0) else "").strip()
            name = (self.lines_table.item(r, 1).text() if self.lines_table.item(r, 1) else "").strip()
            dr = max(0, _parse_paise(self.lines_table.item(r, 2).text() if self.lines_table.item(r, 2) else 0))
            cr = max(0, _parse_paise(self.lines_table.item(r, 3).text() if self.lines_table.item(r, 3) else 0))
            narr = (self.lines_table.item(r, 4).text() if self.lines_table.item(r, 4) else "").strip() or None
            if code and (dr > 0 or cr > 0):
                lines.append(CreateAJELineDTO(account_code=code, account_name=name or code, debit_paise=dr, credit_paise=cr, narration=narr))
        return lines

    def _on_save_clicked(self) -> None:
        if not self.aje_num_input.text().strip() or not self.title_input.text().strip() or not self.reason_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "AJE Number, Title, and Reason are required.")
            return
        lines = self._collect_lines()
        if len(lines) < 2 or sum(l.debit_paise for l in lines) != sum(l.credit_paise for l in lines) or sum(l.debit_paise for l in lines) <= 0:
            QMessageBox.warning(self, "Double-Entry Violation", "Debits must equal Credits > 0 with at least 2 lines.")
            return
        try:
            if self.existing_entry:
                self.saved_entry = self.adjustment_service.update_draft_adjustment(
                    UpdateAJEDTO(
                        engagement_id=self.engagement_id,
                        entry_id=self.existing_entry.id,
                        title=self.title_input.text().strip(),
                        narration=self.narration_input.text().strip() or self.title_input.text().strip(),
                        reason=self.reason_input.text().strip(),
                        working_paper_ref=self.wp_ref_input.text().strip() or None,
                        aje_type=self.type_combo.currentData(),
                        lines=lines,
                    )
                )
            else:
                self.saved_entry = self.adjustment_service.create_adjustment(
                    CreateAJEDTO(
                        engagement_id=self.engagement_id,
                        aje_number=self.aje_num_input.text().strip(),
                        entry_date=self.date_input.date().toString("yyyy-MM-dd"),
                        title=self.title_input.text().strip(),
                        narration=self.narration_input.text().strip() or self.title_input.text().strip(),
                        reason=self.reason_input.text().strip(),
                        working_paper_ref=self.wp_ref_input.text().strip() or None,
                        aje_type=self.type_combo.currentData(),
                        lines=lines,
                    )
                )
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def _on_submit_clicked(self) -> None:
        self._on_save_clicked()
        if self.saved_entry:
            try:
                self.adjustment_service.submit_adjustment(
                    SubmitAJEDTO(engagement_id=self.engagement_id, entry_id=self.saved_entry.id)
                )
            except Exception as ex:
                QMessageBox.critical(self, "Error Submitting", str(ex))
