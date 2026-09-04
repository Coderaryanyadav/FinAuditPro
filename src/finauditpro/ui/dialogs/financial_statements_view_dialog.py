"""UI Dialog for Schedule III Financial Statements, Notes, Cash Flow, CARO 2020, and Form 3CD."""

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

from finauditpro.application.financial_statement_dtos import (
    GenerateFinancialStatementsDTO,
    GetDataLineageDTO,
    LockFinancialStatementPackageDTO,
    ReviewFinancialStatementPackageDTO,
    SaveFinancialStatementPackageDTO,
)
from finauditpro.application.services.compliance_service import ComplianceService
from finauditpro.application.services.financial_statement_service import FinancialStatementService


class FinancialStatementsViewDialog(QDialog):
    """Multi-tab professional viewer for Schedule III Financial Statements and Compliance."""

    def __init__(
        self, db_manager: Any, engagement_id: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.engagement_id = engagement_id
        self.fs_service = FinancialStatementService(db_manager)
        self.comp_service = ComplianceService(db_manager)

        self.setWindowTitle("Schedule III Financial Statements & Indian Compliance — FinAuditPro")
        self.resize(1100, 750)
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header & Action Bar
        top_bar = QHBoxLayout()
        self.lbl_status = QLabel("Financial Statements Status: Ready")
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 14px; color: #1e293b;")
        top_bar.addWidget(self.lbl_status)
        top_bar.addStretch()

        self.btn_refresh = QPushButton("Refresh Statements")
        self.btn_refresh.clicked.connect(self._load_data)
        top_bar.addWidget(self.btn_refresh)

        self.btn_save_pkg = QPushButton("Save Package (Draft V1)")
        self.btn_save_pkg.clicked.connect(self._save_package)
        top_bar.addWidget(self.btn_save_pkg)

        self.btn_approve_pkg = QPushButton("Approve Package")
        self.btn_approve_pkg.clicked.connect(self._approve_package)
        top_bar.addWidget(self.btn_approve_pkg)

        self.btn_lock_pkg = QPushButton("Lock Final Package")
        self.btn_lock_pkg.setStyleSheet(
            "background-color: #dc2626; color: white; font-weight: bold;"
        )
        self.btn_lock_pkg.clicked.connect(self._lock_package)
        top_bar.addWidget(self.btn_lock_pkg)

        layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_bs = QWidget()
        self.tab_pnl = QWidget()
        self.tab_cf = QWidget()
        self.tab_notes = QWidget()
        self.tab_caro = QWidget()
        self.tab_tax = QWidget()

        self._setup_bs_tab()
        self._setup_pnl_tab()
        self._setup_cf_tab()
        self._setup_notes_tab()
        self._setup_caro_tab()
        self._setup_tax_tab()

        self.tabs.addTab(self.tab_bs, "1. Balance Sheet")
        self.tabs.addTab(self.tab_pnl, "2. Statement of Profit & Loss")
        self.tabs.addTab(self.tab_cf, "3. Cash Flow Statement")
        self.tabs.addTab(self.tab_notes, "4. Notes to Accounts")
        self.tabs.addTab(self.tab_caro, "5. CARO 2020 Workpapers")
        self.tabs.addTab(self.tab_tax, "6. Form 3CD Tax Audit")

        layout.addWidget(self.tabs)

    def _setup_bs_tab(self) -> None:
        v = QVBoxLayout(self.tab_bs)
        self.lbl_bs_reconcile = QLabel("Balance Sheet Balance Status: Calculating...")
        self.lbl_bs_reconcile.setStyleSheet(
            "font-weight: bold; padding: 6px; background-color: #f1f5f9; border-radius: 4px;"
        )
        v.addWidget(self.lbl_bs_reconcile)

        self.tbl_bs = QTableWidget(0, 5)
        self.tbl_bs.setHorizontalHeaderLabels(
            [
                "Line Code",
                "Schedule III Category",
                "Line Item Description",
                "Note Ref",
                "Current Year (₹)",
            ]
        )
        self.tbl_bs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(self.tbl_bs)

        h = QHBoxLayout()
        self.btn_lineage = QPushButton("Inspect Lineage for Selected Line")
        self.btn_lineage.clicked.connect(self._show_lineage)
        h.addWidget(self.btn_lineage)
        h.addStretch()
        v.addLayout(h)

    def _setup_pnl_tab(self) -> None:
        v = QVBoxLayout(self.tab_pnl)
        self.lbl_pnl_summary = QLabel("Profit & Loss Summary")
        self.lbl_pnl_summary.setStyleSheet(
            "font-weight: bold; padding: 6px; background-color: #f1f5f9; border-radius: 4px;"
        )
        v.addWidget(self.lbl_pnl_summary)

        self.tbl_pnl = QTableWidget(0, 4)
        self.tbl_pnl.setHorizontalHeaderLabels(
            ["Line Code", "Category / Line Item", "Note Ref", "Amount (₹)"]
        )
        self.tbl_pnl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(self.tbl_pnl)

    def _setup_cf_tab(self) -> None:
        v = QVBoxLayout(self.tab_cf)
        self.lbl_cf_reconcile = QLabel("Cash Flow Reconciliation Status: Checking...")
        self.lbl_cf_reconcile.setStyleSheet(
            "font-weight: bold; padding: 6px; background-color: #f1f5f9; border-radius: 4px;"
        )
        v.addWidget(self.lbl_cf_reconcile)

        self.tbl_cf = QTableWidget(0, 3)
        self.tbl_cf.setHorizontalHeaderLabels(
            ["Activity Type", "Cash Flow Description", "Amount (₹)"]
        )
        self.tbl_cf.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(self.tbl_cf)

    def _setup_notes_tab(self) -> None:
        v = QVBoxLayout(self.tab_notes)
        self.tbl_notes = QTableWidget(0, 5)
        self.tbl_notes.setHorizontalHeaderLabels(
            ["Note No", "Title", "FS Ref", "Classification", "Total Amount (₹)"]
        )
        self.tbl_notes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(self.tbl_notes)

    def _setup_caro_tab(self) -> None:
        v = QVBoxLayout(self.tab_caro)
        self.tbl_caro = QTableWidget(0, 5)
        self.tbl_caro.setHorizontalHeaderLabels(
            ["Clause", "Title", "Applicability", "Report Answer", "Status"]
        )
        self.tbl_caro.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(self.tbl_caro)

    def _setup_tax_tab(self) -> None:
        v = QVBoxLayout(self.tab_tax)
        self.lbl_tax_summary = QLabel("Form 3CD Checks Summary")
        self.lbl_tax_summary.setStyleSheet(
            "font-weight: bold; padding: 6px; background-color: #f1f5f9; border-radius: 4px;"
        )
        v.addWidget(self.lbl_tax_summary)

        self.tbl_tax = QTableWidget(0, 5)
        self.tbl_tax.setHorizontalHeaderLabels(
            ["Clause", "Category", "Description", "Result", "Exception (₹)"]
        )
        self.tbl_tax.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(self.tbl_tax)

    def _load_data(self) -> None:
        dto = GenerateFinancialStatementsDTO(engagement_id=self.engagement_id)
        bs = self.fs_service.generate_balance_sheet(dto)
        pnl = self.fs_service.generate_profit_and_loss(dto)
        cf = self.fs_service.generate_cash_flow_statement(dto)

        # 1. Populate Balance Sheet Table
        self.tbl_bs.setRowCount(0)
        all_bs = (
            [("--- EQUITY & LIABILITIES ---", None)]
            + [(l.line_code, l) for l in bs.equity_and_liabilities_lines]
            + [("--- ASSETS ---", None)]
            + [(l.line_code, l) for l in bs.assets_lines]
        )
        for code, l in all_bs:
            r = self.tbl_bs.rowCount()
            self.tbl_bs.insertRow(r)
            if l is None:
                it = QTableWidgetItem(code)
                it.setTextAlignment(Qt.AlignCenter)
                it.setBackground(Qt.lightGray)
                self.tbl_bs.setItem(r, 1, it)
            else:
                self.tbl_bs.setItem(r, 0, QTableWidgetItem(l.line_code))
                self.tbl_bs.setItem(r, 1, QTableWidgetItem(l.category))
                self.tbl_bs.setItem(r, 2, QTableWidgetItem(l.line_item))
                self.tbl_bs.setItem(r, 3, QTableWidgetItem(l.note_ref or ""))
                self.tbl_bs.setItem(r, 4, QTableWidgetItem(f"₹{l.current_period_paise / 100:,.2f}"))

        bal_str = (
            "BALANCED (₹0.00 Difference)"
            if bs.is_balanced
            else f"UNBALANCED (Diff: ₹{bs.difference_paise / 100:,.2f})"
        )
        color = "#16a34a" if bs.is_balanced else "#dc2626"
        self.lbl_bs_reconcile.setText(
            f"Total Equity & Liabilities: ₹{bs.total_equity_and_liabilities_paise / 100:,.2f} | Total Assets: ₹{bs.total_assets_paise / 100:,.2f} | {bal_str}"
        )
        self.lbl_bs_reconcile.setStyleSheet(
            f"font-weight: bold; padding: 6px; background-color: #f1f5f9; color: {color}; border-radius: 4px;"
        )

        # 2. Populate P&L Table
        self.tbl_pnl.setRowCount(0)
        for l in pnl.revenue_lines + pnl.expense_lines:
            r = self.tbl_pnl.rowCount()
            self.tbl_pnl.insertRow(r)
            self.tbl_pnl.setItem(r, 0, QTableWidgetItem(l.line_code))
            self.tbl_pnl.setItem(r, 1, QTableWidgetItem(f"{l.category} — {l.line_item}"))
            self.tbl_pnl.setItem(r, 2, QTableWidgetItem(l.note_ref or ""))
            self.tbl_pnl.setItem(r, 3, QTableWidgetItem(f"₹{l.current_period_paise / 100:,.2f}"))

        self.lbl_pnl_summary.setText(
            f"Total Revenue: ₹{pnl.total_revenue_paise / 100:,.2f} | Total Expenses: ₹{pnl.total_expenses_paise / 100:,.2f} | Profit After Tax (PAT): ₹{pnl.profit_after_tax_paise / 100:,.2f}"
        )

        # 3. Populate Cash Flow Table
        self.tbl_cf.setRowCount(0)
        for l in cf.operating_activities + cf.investing_activities + cf.financing_activities:
            r = self.tbl_cf.rowCount()
            self.tbl_cf.insertRow(r)
            self.tbl_cf.setItem(r, 0, QTableWidgetItem(l.activity_type.value))
            self.tbl_cf.setItem(r, 1, QTableWidgetItem(l.description))
            self.tbl_cf.setItem(r, 2, QTableWidgetItem(f"₹{l.amount_paise / 100:,.2f}"))

        cf_rec_str = (
            "RECONCILED WITH BALANCE SHEET CASH"
            if cf.is_reconciled
            else f"NOT RECONCILED (Diff: ₹{cf.reconciliation_difference_paise / 100:,.2f})"
        )
        cf_color = "#16a34a" if cf.is_reconciled else "#dc2626"
        self.lbl_cf_reconcile.setText(
            f"Net Operating: ₹{cf.net_cash_from_operating_paise / 100:,.2f} | Net Investing: ₹{cf.net_cash_from_investing_paise / 100:,.2f} | Net Financing: ₹{cf.net_cash_from_financing_paise / 100:,.2f} | Closing Cash: ₹{cf.closing_cash_and_equivalents_paise / 100:,.2f} | {cf_rec_str}"
        )
        self.lbl_cf_reconcile.setStyleSheet(
            f"font-weight: bold; padding: 6px; background-color: #f1f5f9; color: {cf_color}; border-radius: 4px;"
        )

        # 4. Populate CARO Table
        caros = self.comp_service.initialize_caro_clauses(self.engagement_id)
        self.tbl_caro.setRowCount(0)
        for c in caros:
            r = self.tbl_caro.rowCount()
            self.tbl_caro.insertRow(r)
            self.tbl_caro.setItem(r, 0, QTableWidgetItem(c.clause_code))
            self.tbl_caro.setItem(r, 1, QTableWidgetItem(c.clause_title))
            self.tbl_caro.setItem(
                r,
                2,
                QTableWidgetItem(
                    c.applicability.value
                    if hasattr(c.applicability, "value")
                    else str(c.applicability)
                ),
            )
            self.tbl_caro.setItem(
                r,
                3,
                QTableWidgetItem(
                    c.report_answer.value
                    if hasattr(c.report_answer, "value")
                    else str(c.report_answer)
                ),
            )
            self.tbl_caro.setItem(r, 4, QTableWidgetItem(c.status))

    def _show_lineage(self) -> None:
        row = self.tbl_bs.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select a line item in the Balance Sheet table."
            )
            return
        code_item = self.tbl_bs.item(row, 0)
        if not code_item or not code_item.text():
            return
        lineage = self.fs_service.get_data_lineage(
            GetDataLineageDTO(engagement_id=self.engagement_id, line_code=code_item.text())
        )
        lines_msg = f"Line Item: {lineage.fs_line_code} ({lineage.fs_line_name})\nTotal: ₹{lineage.total_amount_paise / 100:,.2f}\nNote: {lineage.note_ref or 'N/A'}\n\nMapped Accounts:\n"
        for t in lineage.account_traces:
            lines_msg += f"- {t['account_code']}: {t['account_name']} (Adj Net: ₹{t['adjusted_net_paise'] / 100:,.2f}, AJEs: {t.get('linked_aje_numbers', [])})\n"
        QMessageBox.information(self, f"Data Lineage — {lineage.fs_line_code}", lines_msg)

    def _save_package(self) -> None:
        try:
            pkg = self.fs_service.save_package(
                SaveFinancialStatementPackageDTO(engagement_id=self.engagement_id)
            )
            QMessageBox.information(
                self,
                "Saved",
                f"Financial Statement Package saved successfully as {pkg.version.value}.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _approve_package(self) -> None:
        try:
            latest = self.fs_service.save_package(
                SaveFinancialStatementPackageDTO(engagement_id=self.engagement_id)
            )
            pkg = self.fs_service.review_package(
                ReviewFinancialStatementPackageDTO(
                    engagement_id=self.engagement_id, package_id=latest.id, decision="APPROVE"
                )
            )
            QMessageBox.information(
                self, "Approved", f"Package approved by reviewer: {pkg.status.value}."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _lock_package(self) -> None:
        try:
            latest = self.fs_service.save_package(
                SaveFinancialStatementPackageDTO(engagement_id=self.engagement_id)
            )
            self.fs_service.review_package(
                ReviewFinancialStatementPackageDTO(
                    engagement_id=self.engagement_id, package_id=latest.id, decision="APPROVE"
                )
            )
            pkg = self.fs_service.lock_package(
                LockFinancialStatementPackageDTO(
                    engagement_id=self.engagement_id, package_id=latest.id
                )
            )
            QMessageBox.information(
                self, "Locked", f"Package sealed and locked: {pkg.status.value}."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
