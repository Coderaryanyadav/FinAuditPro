"""CA-oriented interactive Audit Adjusting Journal Entries (AJE) and Lead Schedule Dialog."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.audit_adjustment_dtos import (
    ApplyAJEDTO,
    ReverseAJEDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
)
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.domain.audit_adjustment_entities import AJEStatusEnum, AuditJournalEntry
from finauditpro.ui.dialogs.create_aje_dialog import CreateAJEDialog
from finauditpro.ui.dialogs.lead_schedule_trace_dialog import LeadScheduleTraceDialog
from finauditpro.ui.theme import format_inr


class AuditAdjustmentDialog(QDialog):
    """Practical CA interface for managing AJEs, Adjusted Trial Balance, and Lead Schedules."""

    def __init__(
        self,
        adjustment_service: AuditAdjustmentService,
        engagement_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.adjustment_service = adjustment_service
        self.engagement_id = engagement_id
        self.ajes: list[AuditJournalEntry] = []

        self.setWindowTitle("Audit Adjustment Journals (AJE) & Lead Schedules")
        self.resize(1180, 720)
        self.setModal(True)

        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.tabs = QTabWidget()

        # Tab 1: AJEs
        aje_tab = QWidget()
        aje_layout = QVBoxLayout(aje_tab)
        toolbar = QHBoxLayout()
        self.new_aje_btn = QPushButton("+ New AJE")
        self.new_aje_btn.setObjectName("primaryButton")
        self.new_aje_btn.clicked.connect(self._on_new_aje_clicked)
        toolbar.addWidget(self.new_aje_btn)

        self.edit_btn = QPushButton("Edit Draft")
        self.edit_btn.clicked.connect(self._on_edit_draft_clicked)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete Draft")
        self.delete_btn.clicked.connect(self._on_delete_draft_clicked)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self._on_submit_clicked)
        toolbar.addWidget(self.submit_btn)

        self.approve_btn = QPushButton("Approve (Maker-Checker)")
        self.approve_btn.clicked.connect(self._on_approve_clicked)
        toolbar.addWidget(self.approve_btn)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        toolbar.addWidget(self.apply_btn)

        self.reverse_btn = QPushButton("Reverse")
        self.reverse_btn.clicked.connect(self._on_reverse_clicked)
        toolbar.addWidget(self.reverse_btn)
        aje_layout.addLayout(toolbar)

        self.aje_table = QTableWidget(0, 8)
        self.aje_table.setHorizontalHeaderLabels(
            ["AJE #", "DATE", "TYPE", "STATUS", "TITLE", "DEBIT (₹)", "CREDIT (₹)", "PREPARED BY"]
        )
        self.aje_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for c in (0, 1, 2, 3, 5, 6, 7):
            self.aje_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.aje_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.aje_table.verticalHeader().setVisible(False)
        self.aje_table.setAlternatingRowColors(True)
        self.aje_table.cellDoubleClicked.connect(self._on_aje_double_clicked)
        aje_layout.addWidget(self.aje_table)
        self.tabs.addTab(aje_tab, "Audit Adjustments (AJE Register)")

        # Tab 2: Adjusted TB
        tb_tab = QWidget()
        tb_layout = QVBoxLayout(tb_tab)
        self.tb_summary_lbl = QLabel("Adjusted Trial Balance Summary")
        self.tb_summary_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        tb_layout.addWidget(self.tb_summary_lbl)

        self.tb_table = QTableWidget(0, 8)
        self.tb_table.setHorizontalHeaderLabels(
            ["ACCOUNT CODE", "ACCOUNT NAME", "UNADJ DR (₹)", "UNADJ CR (₹)", "AJE DR (₹)", "AJE CR (₹)", "ADJ DR (₹)", "ADJ CR (₹)"]
        )
        self.tb_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in (0, 2, 3, 4, 5, 6, 7):
            self.tb_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.tb_table.verticalHeader().setVisible(False)
        self.tb_table.setAlternatingRowColors(True)
        tb_layout.addWidget(self.tb_table)
        self.tabs.addTab(tb_tab, "Adjusted Trial Balance")

        # Tab 3: Lead Schedules
        ls_tab = QWidget()
        ls_layout = QVBoxLayout(ls_tab)
        ls_toolbar = QHBoxLayout()
        self.trace_ls_btn = QPushButton("Trace Lineage")
        self.trace_ls_btn.setObjectName("primaryButton")
        self.trace_ls_btn.clicked.connect(self._on_trace_lead_schedule_clicked)
        ls_toolbar.addWidget(self.trace_ls_btn)
        ls_toolbar.addStretch()
        ls_layout.addLayout(ls_toolbar)

        self.ls_table = QTableWidget(0, 6)
        self.ls_table.setHorizontalHeaderLabels(
            ["REF", "SCHEDULE III CATEGORY", "ACCOUNTS", "UNADJUSTED (₹)", "NET AJE (₹)", "ADJUSTED BALANCE (₹)"]
        )
        self.ls_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in (0, 2, 3, 4, 5):
            self.ls_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.ls_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ls_table.verticalHeader().setVisible(False)
        self.ls_table.setAlternatingRowColors(True)
        self.ls_table.cellDoubleClicked.connect(self._on_trace_lead_schedule_clicked)
        ls_layout.addWidget(self.ls_table)
        self.tabs.addTab(ls_tab, "Lead Schedules Rollup")

        layout.addWidget(self.tabs, 1)
        bottom = QHBoxLayout()
        bottom.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _get_available_accounts(self) -> list[dict[str, str]]:
        try:
            mappings = AccountMappingService(self.adjustment_service.db_manager).list_mappings(self.engagement_id)
            return [{"account_code": m.account_code, "account_name": m.account_name} for m in mappings]
        except Exception:
            return []

    def _load_data(self) -> None:
        self.ajes = self.adjustment_service.list_adjustments(self.engagement_id)
        self._render_ajes()
        self._render_adjusted_tb()
        self._render_lead_schedules()

    def _render_ajes(self) -> None:
        self.aje_table.setRowCount(len(self.ajes))
        for row, aje in enumerate(self.ajes):
            self.aje_table.setItem(row, 0, QTableWidgetItem(aje.aje_number))
            self.aje_table.setItem(row, 1, QTableWidgetItem(aje.entry_date))
            self.aje_table.setItem(row, 2, QTableWidgetItem(str(aje.aje_type)))
            st_item = QTableWidgetItem(str(aje.status))
            if aje.status in (AJEStatusEnum.APPROVED, AJEStatusEnum.APPLIED):
                st_item.setForeground(Qt.GlobalColor.darkGreen)
            elif aje.status == AJEStatusEnum.REJECTED:
                st_item.setForeground(Qt.GlobalColor.red)
            self.aje_table.setItem(row, 3, st_item)
            self.aje_table.setItem(row, 4, QTableWidgetItem(aje.title))
            self.aje_table.setItem(row, 5, QTableWidgetItem(format_inr(aje.total_debit_paise)))
            self.aje_table.setItem(row, 6, QTableWidgetItem(format_inr(aje.total_credit_paise)))
            self.aje_table.setItem(row, 7, QTableWidgetItem(aje.prepared_by))

    def _render_adjusted_tb(self) -> None:
        s = self.adjustment_service.calculate_adjusted_trial_balance(self.engagement_id)
        self.tb_summary_lbl.setText(
            f"Unadjusted: ₹{s.total_unadjusted_dr_paise/100:,.2f} | Net AJE: ₹{s.total_adjustment_dr_paise/100:,.2f} | Final Adjusted: ₹{s.total_adjusted_dr_paise/100:,.2f} (Balanced: {'YES' if s.is_fully_balanced else 'NO'})"
        )
        self.tb_table.setRowCount(len(s.lines))
        for row, l in enumerate(s.lines):
            self.tb_table.setItem(row, 0, QTableWidgetItem(l.account_code))
            self.tb_table.setItem(row, 1, QTableWidgetItem(l.account_name))
            self.tb_table.setItem(row, 2, QTableWidgetItem(format_inr(l.unadjusted_dr_paise)))
            self.tb_table.setItem(row, 3, QTableWidgetItem(format_inr(l.unadjusted_cr_paise)))
            self.tb_table.setItem(row, 4, QTableWidgetItem(format_inr(l.adjustment_dr_paise)))
            self.tb_table.setItem(row, 5, QTableWidgetItem(format_inr(l.adjustment_cr_paise)))
            self.tb_table.setItem(row, 6, QTableWidgetItem(format_inr(l.adjusted_dr_paise)))
            self.tb_table.setItem(row, 7, QTableWidgetItem(format_inr(l.adjusted_cr_paise)))

    def _render_lead_schedules(self) -> None:
        schedules = self.adjustment_service.calculate_lead_schedules(self.engagement_id)
        self.ls_table.setRowCount(len(schedules))
        for row, s in enumerate(schedules):
            self.ls_table.setItem(row, 0, QTableWidgetItem(s.lead_schedule_ref))
            self.ls_table.setItem(row, 1, QTableWidgetItem(s.category))
            self.ls_table.setItem(row, 2, QTableWidgetItem(str(s.account_count)))
            self.ls_table.setItem(row, 3, QTableWidgetItem(format_inr(s.unadjusted_balance_paise)))
            self.ls_table.setItem(row, 4, QTableWidgetItem(format_inr(s.net_adjustment_paise)))
            self.ls_table.setItem(row, 5, QTableWidgetItem(format_inr(s.adjusted_balance_paise)))

    def _get_selected_aje(self) -> AuditJournalEntry | None:
        row = self.aje_table.currentRow()
        return self.ajes[row] if 0 <= row < len(self.ajes) else None

    def _on_new_aje_clicked(self) -> None:
        accounts = self._get_available_accounts()
        dlg = CreateAJEDialog(self.adjustment_service, self.engagement_id, available_accounts=accounts, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_data()

    def _on_edit_draft_clicked(self) -> None:
        aje = self._get_selected_aje()
        if not aje:
            return
        if aje.status not in (AJEStatusEnum.DRAFT, AJEStatusEnum.REJECTED):
            QMessageBox.warning(self, "Cannot Edit", "Only Draft or Rejected adjustments can be edited.")
            return
        accounts = self._get_available_accounts()
        dlg = CreateAJEDialog(self.adjustment_service, self.engagement_id, existing_entry=aje, available_accounts=accounts, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_data()

    def _on_delete_draft_clicked(self) -> None:
        aje = self._get_selected_aje()
        if not aje or aje.status != AJEStatusEnum.DRAFT:
            QMessageBox.warning(self, "Cannot Delete", "Only Draft adjustments can be deleted.")
            return
        if QMessageBox.question(self, "Confirm", f"Delete draft AJE '{aje.aje_number}'?") == QMessageBox.StandardButton.Yes:
            self.adjustment_service.delete_draft_adjustment(self.engagement_id, aje.id)
            self._load_data()

    def _on_aje_double_clicked(self, row: int, col: int) -> None:
        if 0 <= row < len(self.ajes):
            aje = self.ajes[row]
            if aje.status in (AJEStatusEnum.DRAFT, AJEStatusEnum.REJECTED):
                self._on_edit_draft_clicked()
            else:
                lines_str = "\n".join(f"  - {l.account_code}: Dr ₹{l.debit_paise/100:,.2f} | Cr ₹{l.credit_paise/100:,.2f}" for l in aje.lines)
                QMessageBox.information(self, f"AJE Details: {aje.aje_number}", f"Title: {aje.title}\nStatus: {aje.status}\n\nLines:\n{lines_str}")

    def _on_submit_clicked(self) -> None:
        aje = self._get_selected_aje()
        if aje:
            try:
                self.adjustment_service.submit_adjustment(SubmitAJEDTO(engagement_id=self.engagement_id, entry_id=aje.id))
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_approve_clicked(self) -> None:
        aje = self._get_selected_aje()
        if aje:
            try:
                self.adjustment_service.review_adjustment(ReviewAJEDTO(engagement_id=self.engagement_id, entry_id=aje.id, decision="APPROVE"))
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_apply_clicked(self) -> None:
        aje = self._get_selected_aje()
        if aje:
            try:
                self.adjustment_service.apply_adjustment(ApplyAJEDTO(engagement_id=self.engagement_id, entry_id=aje.id))
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_reverse_clicked(self) -> None:
        aje = self._get_selected_aje()
        if aje:
            try:
                self.adjustment_service.reverse_adjustment(ReverseAJEDTO(engagement_id=self.engagement_id, entry_id=aje.id, reversal_aje_number=f"REV-{aje.aje_number}", reason="Reversal"))
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_trace_lead_schedule_clicked(self) -> None:
        row = self.ls_table.currentRow()
        if row >= 0 and self.ls_table.item(row, 0):
            ref = self.ls_table.item(row, 0).text()
            LeadScheduleTraceDialog(self.adjustment_service, self.engagement_id, ref, parent=self).exec()
