from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

from finauditpro.application.roll_forward_dtos import ConfirmTieOutDTO
from finauditpro.application.services.roll_forward_service import RollForwardService
from finauditpro.ui.dialogs.roll_forward_wizard_dialog import RollForwardWizardDialog


class RollForwardView(QWidget):
    """Workspace view displaying SA 510 opening balance tie-outs, comparatives, and roll-forward triggers."""

    def __init__(self, db_manager: Any, parent=None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.roll_forward_service = RollForwardService(db_manager)
        self.current_engagement_id: str | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header & Roll Forward Button
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("<h2>Multi-Year Continuity & SA 510 Opening Balance Tie-Out</h2>"))
        top_layout.addStretch()

        self.confirm_tieout_btn = QPushButton("✓ Confirm Tie-Out (Auditor)")
        self.confirm_tieout_btn.setStyleSheet("background-color: #276749; color: white; font-weight: bold; padding: 6px 12px;")
        self.confirm_tieout_btn.clicked.connect(self._confirm_tie_out)
        top_layout.addWidget(self.confirm_tieout_btn)

        layout.addLayout(top_layout)

        # Status Banner
        self.banner_frame = QFrame()
        self.banner_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.banner_frame.setStyleSheet("background-color: #332b00; border: 1px solid #78350f; border-radius: 6px; padding: 12px;")
        banner_layout = QVBoxLayout(self.banner_frame)

        self.tieout_summary_label = QLabel("<b>SA 510 Opening Balance Tie-Out Status:</b> Pending Calculation [verified: false]")
        self.tieout_summary_label.setStyleSheet("color: #fef08a; font-size: 13px;")

        self.disclaimer_label = QLabel("<i>Notice: SA 510 opening balance tie-out checks prior closing vs current opening. Auditor confirmation is required.</i>")
        self.disclaimer_label.setStyleSheet("color: #fef9c3; font-size: 12px;")

        banner_layout.addWidget(self.tieout_summary_label)
        banner_layout.addWidget(self.disclaimer_label)
        layout.addWidget(self.banner_frame)

        # Opening Balance Tie-Out Table
        layout.addWidget(QLabel("<b>Account-by-Account SA 510 Opening Balance Tie-Out:</b>"))
        self.tieout_table = QTableWidget()
        self.tieout_table.setColumnCount(7)
        self.tieout_table.setHorizontalHeaderLabels([
            "Account Code",
            "Account Name",
            "Opening DR (₹)",
            "Opening CR (₹)",
            "Prior Closing DR (₹)",
            "Prior Closing CR (₹)",
            "Tie-Out Status",
        ])
        self.tieout_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tieout_table)

    def load_engagement(self, engagement_id: str) -> None:
        self.current_engagement_id = engagement_id
        self._refresh_view()

    def _refresh_view(self) -> None:
        if not self.current_engagement_id:
            return

        summary, links = self.roll_forward_service.get_opening_balance_tie_out(self.current_engagement_id)

        verified_str = "Confirmed by Auditor" if summary.is_confirmed_by_auditor else "Unconfirmed [verified: false]"
        tied_str = "All Accounts Tied Out ✅" if summary.is_fully_tied_out else f"Mismatches Detected ({summary.mismatched_accounts} account(s)) ⚠️"

        self.tieout_summary_label.setText(
            f"<b>SA 510 Tie-Out Status:</b> {tied_str} | "
            f"Total Accounts: {summary.total_accounts} | "
            f"Auditor Verification: {verified_str}"
        )

        self.tieout_table.setRowCount(len(links))
        for row, link in enumerate(links):
            op_dr_rs = link.opening_dr_paise / 100.0
            op_cr_rs = link.opening_cr_paise / 100.0
            cl_dr_rs = link.prior_closing_dr_paise / 100.0
            cl_cr_rs = link.prior_closing_cr_paise / 100.0

            status_item = QTableWidgetItem("Tied Out ✅" if link.is_tied_out else "MISMATCH ⚠️")
            if not link.is_tied_out:
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkGreen)

            self.tieout_table.setItem(row, 0, QTableWidgetItem(link.account_code))
            self.tieout_table.setItem(row, 1, QTableWidgetItem(link.account_name))
            self.tieout_table.setItem(row, 2, QTableWidgetItem(f"{op_dr_rs:,.2f}"))
            self.tieout_table.setItem(row, 3, QTableWidgetItem(f"{op_cr_rs:,.2f}"))
            self.tieout_table.setItem(row, 4, QTableWidgetItem(f"{cl_dr_rs:,.2f}"))
            self.tieout_table.setItem(row, 5, QTableWidgetItem(f"{cl_cr_rs:,.2f}"))
            self.tieout_table.setItem(row, 6, status_item)

    def _confirm_tie_out(self) -> None:
        if not self.current_engagement_id:
            return

        summary, _ = self.roll_forward_service.get_opening_balance_tie_out(self.current_engagement_id)
        if summary.total_accounts == 0:
            QMessageBox.information(self, "No Links", "No opening balance links exist for this engagement.")
            return

        self.roll_forward_service.confirm_opening_balance_tie_out(
            ConfirmTieOutDTO(
                engagement_id=self.current_engagement_id,
                auditor_name="Audit Senior",
            )
        )
        QMessageBox.information(self, "Tie-Out Confirmed", "SA 510 opening balance tie-out confirmed by auditor.")
        self._refresh_view()
