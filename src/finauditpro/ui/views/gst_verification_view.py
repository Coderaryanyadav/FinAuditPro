from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.domain.entities import Engagement
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, MetricCard, PageHeader, format_inr


class GSTVerificationView(QWidget):
    """Enterprise GST Reconciliation & ITC Verification Workspace Widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_engagement: Engagement | None = None
        self._invoices: list[tuple[Any, ...]] = []
        self._init_ui()

    def set_active_engagement(self, engagement: Any) -> None:
        self.current_engagement = (
            engagement if isinstance(engagement, Engagement) or engagement else None
        )
        self._load_engagement_gst_data()
        self.load_data()

    set_engagement = set_active_engagement

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(14)

        self.header = PageHeader(
            title="GST Reconciliation",
            subtitle="Compare purchase register entries against GSTR-2B and audit statutory ITC claims (Sec 16/17).",
            action_text="Run GST Matching",
            action_callback=self._run_matching,
        )
        main_layout.addWidget(self.header)

        stats = QHBoxLayout()
        stats.setSpacing(10)
        self.card_total = MetricCard(
            "TOTAL INVOICES", "0", "Purchase register entries", accent_color="#0284C7"
        )
        self.card_matched = MetricCard(
            "MATCHED IN 2B", "0", "Full credit available", accent_color="#16A34A"
        )
        self.card_mismatch = MetricCard(
            "MISMATCHED / MISSING", "0", "Action required", accent_color="#DC2626"
        )
        self.card_ineligible = MetricCard(
            "INELIGIBLE SEC 17(5)", "0", "Blocked ITC claims", accent_color="#D97706"
        )
        for c in (self.card_total, self.card_matched, self.card_mismatch, self.card_ineligible):
            stats.addWidget(c)
        main_layout.addLayout(stats)

        self.table_card = CardWidget("GST RECONCILIATION INVOICES")
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "INVOICE NO",
                "DATE",
                "VENDOR NAME",
                "GSTIN",
                "TAXABLE AMT (₹)",
                "BOOKS ITC (₹)",
                "2B ITC (₹)",
                "VARIANCE (₹)",
                "RECON STATUS",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for col_idx in [0, 1, 3, 4, 5, 6, 7, 8]:
            self.table.horizontalHeader().setSectionResizeMode(
                col_idx, QHeaderView.ResizeMode.ResizeToContents
            )

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.empty_state = EmptyStateWidget(
            title="No GST reconciliation records loaded",
            description="Select an active engagement and click 'Run GST Matching' to audit purchase register vs GSTR-2B.",
            action_text="Run GST Matching",
            action_callback=self._run_matching,
        )

        self.table.setVisible(False)
        self.table_card.content_layout.addWidget(self.table)
        self.table_card.content_layout.addWidget(self.empty_state)
        main_layout.addWidget(self.table_card)
        main_layout.addStretch(1)
        self.load_data()

    def _load_engagement_gst_data(self) -> None:
        if not self.current_engagement:
            self._invoices = []
            return

        # Currently no backend database table exists for GST invoices.
        # Fallback to an honest empty state until the feature is fully implemented.
        self._invoices = []

    def _run_matching(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return
        self._load_engagement_gst_data()
        self.load_data()
        if not self._invoices:
            QMessageBox.information(
                self,
                "GST Reconciliation",
                "No purchase register or GSTR-2B datasets have been imported for this engagement yet. Please import GST data to run automated 2B reconciliation.",
            )
        else:
            QMessageBox.information(
                self,
                "Reconciliation Complete",
                f"GST Matching completed across {len(self._invoices)} purchase vouchers against GSTR-2B.",
            )

    def load_data(self) -> None:
        if not self._invoices:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            for c in (self.card_total, self.card_matched, self.card_mismatch, self.card_ineligible):
                c.set_value("0")
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)
        matched_cnt, mismatch_cnt, ineligible_cnt = 0, 0, 0

        for idx, row in enumerate(self._invoices):
            self.table.insertRow(idx)
            status_str = row[8]
            if "matched" in status_str.lower():
                matched_cnt += 1
            elif "ineligible" in status_str.lower():
                ineligible_cnt += 1
            else:
                mismatch_cnt += 1

            for c_idx in range(4):
                self.table.setItem(idx, c_idx, QTableWidgetItem(str(row[c_idx])))
            for c_idx, val in [(4, row[4]), (5, row[5]), (6, row[6]), (7, row[7])]:
                it = QTableWidgetItem(format_inr(val))
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(idx, c_idx, it)
            self.table.setItem(idx, 8, QTableWidgetItem(f"● {row[8]}"))

        self.table.setFixedHeight(max(1, len(self._invoices)) * 36 + 32)
        self.card_total.set_value(str(len(self._invoices)))
        self.card_matched.set_value(str(matched_cnt))
        self.card_mismatch.set_value(str(mismatch_cnt))
        self.card_ineligible.set_value(str(ineligible_cnt))
