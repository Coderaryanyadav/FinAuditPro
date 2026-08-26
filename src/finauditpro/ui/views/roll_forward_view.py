"""
Multi-Year Continuity & SA 510 Opening Balance Tie-Out Workspace View for FinAuditPro.
Verifies prior period closing balances against current period opening balances.
"""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.roll_forward_dtos import ConfirmTieOutDTO
from finauditpro.application.services.roll_forward_service import RollForwardService
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, PageHeader, format_inr


class RollForwardView(QWidget):
    """Workspace view displaying SA 510 opening balance tie-outs, comparatives, and roll-forward triggers."""

    def __init__(self, db_manager: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.db_manager = db_manager
        self.roll_forward_service = RollForwardService(db_manager)
        self.current_engagement_id: str | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Roll-Forward & SA 510 Continuity",
            subtitle="Verify prior period closing balances against current period opening balances per SA 510.",
            action_text="Confirm Tie-Out",
            action_callback=self._confirm_tie_out,
        )
        layout.addWidget(self.header)

        # 2. Status Banner Card
        banner_card = CardWidget("SA 510 TIE-OUT STATUS")
        b_layout = QVBoxLayout()
        b_layout.setSpacing(4)
        self.tieout_summary_label = QLabel("SA 510 Status: Pending Calculation")
        self.tieout_summary_label.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #0F172A; border: none; background: transparent;"
        )
        self.disclaimer_label = QLabel(
            "Notice: SA 510 opening balance tie-out checks prior closing vs current opening. Auditor judgment and confirmation required."
        )
        self.disclaimer_label.setStyleSheet(
            "font-size: 11px; color: #64748B; border: none; background: transparent;"
        )
        b_layout.addWidget(self.tieout_summary_label)
        b_layout.addWidget(self.disclaimer_label)
        banner_card.content_layout.addLayout(b_layout)
        layout.addWidget(banner_card)

        # 3. Opening Balance Tie-Out Table Card & Empty State
        self.table_card = CardWidget("ACCOUNT-BY-ACCOUNT SA 510 OPENING BALANCE TIE-OUT")
        self.tieout_table = QTableWidget()
        self.tieout_table.setColumnCount(7)
        self.tieout_table.setHorizontalHeaderLabels(
            [
                "ACCOUNT CODE",
                "ACCOUNT NAME",
                "OPENING DR (₹)",
                "OPENING CR (₹)",
                "PRIOR CLOSING DR (₹)",
                "PRIOR CLOSING CR (₹)",
                "TIE-OUT STATUS",
            ]
        )
        self.tieout_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in [0, 2, 3, 4, 5, 6]:
            self.tieout_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tieout_table.verticalHeader().setVisible(False)
        self.tieout_table.setAlternatingRowColors(True)

        self.empty_state = EmptyStateWidget(
            title="No opening balance accounts mapped",
            description="Import current and prior year trial balance datasets to calculate automatic SA 510 tie-out continuity.",
            action_text="Confirm Tie-Out",
            action_callback=self._confirm_tie_out,
        )

        self.table_card.content_layout.addWidget(self.tieout_table)
        self.table_card.content_layout.addWidget(self.empty_state)
        layout.addWidget(self.table_card)
        layout.addStretch(1)

    def set_active_engagement(self, engagement: Any) -> None:
        if hasattr(engagement, "id"):
            self.load_engagement(engagement.id)
        elif engagement:
            self.load_engagement(str(engagement))
        else:
            self.current_engagement_id = None
            self._refresh_view()

    def load_engagement(self, engagement_id: str) -> None:
        self.current_engagement_id = engagement_id
        self._refresh_view()

    def _refresh_view(self) -> None:
        if not self.current_engagement_id:
            self.tieout_table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        summary, links = self.roll_forward_service.get_opening_balance_tie_out(
            self.current_engagement_id
        )
        verified_str = "Confirmed by Auditor" if summary.is_confirmed_by_auditor else "Unconfirmed"
        tied_str = (
            "All Accounts Tied Out"
            if summary.is_fully_tied_out
            else f"Mismatches Detected ({summary.mismatched_accounts} account(s))"
        )

        self.tieout_summary_label.setText(
            f"SA 510 Status: {tied_str} · Total Accounts: {summary.total_accounts} · Auditor Verification: {verified_str}"
        )

        if not links:
            self.tieout_table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.tieout_table.setVisible(True)
        self.empty_state.setVisible(False)
        self.tieout_table.setRowCount(len(links))

        for row, link in enumerate(links):
            op_dr_rs = link.opening_dr_paise / 100.0
            op_cr_rs = link.opening_cr_paise / 100.0
            cl_dr_rs = link.prior_closing_dr_paise / 100.0
            cl_cr_rs = link.prior_closing_cr_paise / 100.0

            status_str = "● Tied Out" if link.is_tied_out else "● Mismatch"
            self.tieout_table.setItem(row, 0, QTableWidgetItem(link.account_code))
            self.tieout_table.setItem(row, 1, QTableWidgetItem(link.account_name))

            for c_idx, val in [(2, op_dr_rs), (3, op_cr_rs), (4, cl_dr_rs), (5, cl_cr_rs)]:
                it = QTableWidgetItem(format_inr(val))
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tieout_table.setItem(row, c_idx, it)

            self.tieout_table.setItem(row, 6, QTableWidgetItem(status_str))

        self.tieout_table.setFixedHeight(max(1, len(links)) * 36 + 32)


    def _confirm_tie_out(self) -> None:
        if not self.current_engagement_id:
            return

        summary, _ = self.roll_forward_service.get_opening_balance_tie_out(
            self.current_engagement_id
        )
        if summary.total_accounts == 0:
            QMessageBox.information(
                self, "No Links", "No opening balance links exist for this engagement."
            )
            return

        self.roll_forward_service.confirm_opening_balance_tie_out(
            ConfirmTieOutDTO(engagement_id=self.current_engagement_id, auditor_name="Audit Senior")
        )
        QMessageBox.information(
            self, "Tie-Out Confirmed", "SA 510 opening balance tie-out confirmed by auditor."
        )
        self._refresh_view()
