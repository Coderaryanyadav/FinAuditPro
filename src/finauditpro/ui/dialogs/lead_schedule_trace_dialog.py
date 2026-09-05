"""Dialog rendering detailed bi-directional Lead Schedule & AJE Traceability."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.audit_adjustment_dtos import LeadScheduleTraceDTO
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.ui.theme import CardWidget, format_inr


class LeadScheduleTraceDialog(QDialog):
    """Interactive modal dialog displaying bidirectional traceability from Lead Schedule to TB and AJEs."""

    def __init__(
        self,
        adjustment_service: AuditAdjustmentService,
        engagement_id: str,
        lead_schedule_ref: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.adjustment_service = adjustment_service
        self.engagement_id = engagement_id
        self.lead_schedule_ref = lead_schedule_ref

        self.setWindowTitle(
            f"Lead Schedule Traceability — {lead_schedule_ref} (SA 230 / Schedule III)"
        )
        self.resize(1100, 640)
        self.setModal(True)

        self._init_ui()
        self._load_traceability()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 1. Header Banner
        self.header_lbl = QLabel(f"Traceability Lineage: Lead Schedule {self.lead_schedule_ref}")
        self.header_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #1E293B;")
        layout.addWidget(self.header_lbl)

        self.summary_lbl = QLabel("Loading schedule rollups...")
        self.summary_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #334155; padding: 8px 14px; background: #F1F5F9; border-radius: 6px;"
        )
        layout.addWidget(self.summary_lbl)

        # 2. Splitter: Left = Accounts in this Lead Schedule, Right = Linked AJEs for selected Account
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Accounts Table
        left_card = CardWidget("CONSTITUENT TRIAL BALANCE ACCOUNTS")
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels(
            [
                "CODE",
                "ACCOUNT NAME",
                "UNADJUSTED (₹)",
                "AJE DR (₹)",
                "AJE CR (₹)",
                "ADJUSTED (₹)",
                "AJEs",
            ]
        )
        self.accounts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for c in (0, 2, 3, 4, 5, 6):
            self.accounts_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.itemSelectionChanged.connect(self._on_account_selected)
        left_card.content_layout.addWidget(self.accounts_table)
        splitter.addWidget(left_card)

        # Right: Linked AJEs Table
        right_card = CardWidget("LINKED AUDIT ADJUSTING JOURNAL ENTRIES (AJE)")
        self.aje_detail_lbl = QLabel("Select an account on the left to inspect linked adjustments.")
        self.aje_detail_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-style: italic;")
        right_card.content_layout.addWidget(self.aje_detail_lbl)

        self.aje_table = QTableWidget()
        self.aje_table.setColumnCount(6)
        self.aje_table.setHorizontalHeaderLabels(
            ["AJE #", "DATE", "STATUS", "DEBIT (₹)", "CREDIT (₹)", "NARRATION / TITLE"]
        )
        self.aje_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )
        for c in (0, 1, 2, 3, 4):
            self.aje_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.aje_table.verticalHeader().setVisible(False)
        self.aje_table.setAlternatingRowColors(True)
        right_card.content_layout.addWidget(self.aje_table)
        splitter.addWidget(right_card)

        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        layout.addWidget(splitter, stretch=1)

        # Bottom Actions
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)
        layout.addLayout(bottom_bar)

    def _load_traceability(self) -> None:
        try:
            self.trace_data: LeadScheduleTraceDTO = (
                self.adjustment_service.get_lead_schedule_traceability(
                    self.engagement_id, self.lead_schedule_ref
                )
            )
        except Exception as e:
            self.summary_lbl.setText(f"Error loading trace: {e}")
            return

        self.summary_lbl.setText(
            f"Category: {self.trace_data.category} ({self.trace_data.account_type}) | "
            f"Unadjusted: ₹{self.trace_data.total_unadjusted_paise / 100:,.2f} | "
            f"Net Adjustments: ₹{self.trace_data.total_adjustment_paise / 100:,.2f} | "
            f"Final Adjusted Balance: ₹{self.trace_data.total_adjusted_paise / 100:,.2f} | "
            f"Accounts: {len(self.trace_data.accounts)}"
        )

        self.accounts_table.setRowCount(len(self.trace_data.accounts))
        for row, acc in enumerate(self.trace_data.accounts):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(acc.account_code))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(acc.account_name))
            self.accounts_table.setItem(
                row, 2, QTableWidgetItem(format_inr(acc.unadjusted_net_paise))
            )
            self.accounts_table.setItem(
                row, 3, QTableWidgetItem(format_inr(acc.adjustment_dr_paise))
            )
            self.accounts_table.setItem(
                row, 4, QTableWidgetItem(format_inr(acc.adjustment_cr_paise))
            )
            self.accounts_table.setItem(
                row, 5, QTableWidgetItem(format_inr(acc.adjusted_net_paise))
            )
            self.accounts_table.setItem(row, 6, QTableWidgetItem(str(len(acc.linked_ajes))))

        if self.trace_data.accounts:
            self.accounts_table.selectRow(0)

    def _on_account_selected(self) -> None:
        sel_row = self.accounts_table.currentRow()
        if sel_row < 0 or sel_row >= len(self.trace_data.accounts):
            return

        acc = self.trace_data.accounts[sel_row]
        self.aje_detail_lbl.setText(
            f"Adjustments affecting '{acc.account_code} - {acc.account_name}' ({len(acc.linked_ajes)} entries):"
        )

        self.aje_table.setRowCount(len(acc.linked_ajes))
        for r, aje in enumerate(acc.linked_ajes):
            self.aje_table.setItem(r, 0, QTableWidgetItem(str(aje.get("aje_number", "—"))))
            self.aje_table.setItem(r, 1, QTableWidgetItem(str(aje.get("entry_date", "—"))))
            self.aje_table.setItem(r, 2, QTableWidgetItem(str(aje.get("status", "—"))))
            self.aje_table.setItem(
                r, 3, QTableWidgetItem(format_inr(int(aje.get("debit_paise", 0))))
            )
            self.aje_table.setItem(
                r, 4, QTableWidgetItem(format_inr(int(aje.get("credit_paise", 0))))
            )
            narr = str(aje.get("narration") or aje.get("title") or "—")
            self.aje_table.setItem(r, 5, QTableWidgetItem(narr))
