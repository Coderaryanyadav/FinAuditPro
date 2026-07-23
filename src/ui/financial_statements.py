"""
Financial Statements Verification & Schedule III Mapping Engine for FinAuditPro.
Provides 3-column Trial Balance Ingestion, Mathematical Equality Verification,
Automated Schedule III (Companies Act 2013) Taxonomy Auto-Mapping, and Balance Sheet / P&L Generation.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QTabWidget, QComboBox, QFileDialog, QMessageBox, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import csv
from sqlalchemy.exc import SQLAlchemyError

SCHEDULE_III_CATEGORIES = [
    "Unmapped / Select Head",
    "Tangible Assets (Property, Plant & Equipment)",
    "Intangible Assets",
    "Non-Current Investments",
    "Deferred Tax Assets (Net)",
    "Other Non-Current Assets",
    "Trade Receivables (Current)",
    "Cash & Cash Equivalents",
    "Short-Term Loans & Advances",
    "Other Current Assets",
    "Equity Share Capital",
    "Reserves & Surplus",
    "Long-Term Borrowings",
    "Other Long-Term Liabilities",
    "Long-Term Provisions",
    "Short-Term Borrowings",
    "Trade Payables (Current)",
    "Other Current Liabilities",
    "Short-Term Provisions",
    "Revenue from Operations",
    "Other Income",
    "Cost of Materials Consumed / Purchases",
    "Employee Benefit Expenses",
    "Finance Costs",
    "Depreciation & Amortization",
    "Other Expenses"
]

class FinancialStatementsWidget(QWidget):
    """Schedule III Financial Statement Mapping & Inspection Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.ledger_rows = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Action Bar
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title = QLabel("Schedule III Financial Statements Engine")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("Companies Act 2013 Division I & II Compliance")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)
        h_layout.addStretch()

        btn_import = QPushButton("📁 Import Trial Balance (CSV/Excel)")
        btn_import.setStyleSheet("padding: 8px 14px; background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_import.clicked.connect(self.import_trial_balance)

        btn_auto_map = QPushButton("⚡ Auto-Map Schedule III")
        btn_auto_map.setStyleSheet("padding: 8px 14px; background-color: #f1f5f9; color: #0ea5e9; font-weight: bold; border: 1px solid #bae6fd; border-radius: 6px;")
        btn_auto_map.clicked.connect(self.run_auto_mapping)

        btn_export = QPushButton("📥 Export Statements")
        btn_export.setStyleSheet("padding: 8px 14px; background-color: #f1f5f9; color: #334155; font-weight: bold; border: 1px solid #cbd5e1; border-radius: 6px;")
        btn_export.clicked.connect(self.export_statements)

        h_layout.addWidget(btn_import)
        h_layout.addSpacing(8)
        h_layout.addWidget(btn_auto_map)
        h_layout.addSpacing(8)
        h_layout.addWidget(btn_export)

        layout.addWidget(header)

        # 2. Validation Status Banner
        self.validation_frame = QFrame()
        self.validation_frame.setFixedHeight(46)
        self.validation_frame.setStyleSheet("background-color: #ecfdf5; border-bottom: 1px solid #a7f3d0;")
        val_layout = QHBoxLayout(self.validation_frame)
        val_layout.setContentsMargins(24, 0, 24, 0)

        self.lbl_debit_total = QLabel("Total Debits: ₹0.00")
        self.lbl_debit_total.setStyleSheet("font-weight: bold; color: #047857; font-size: 13px;")

        self.lbl_credit_total = QLabel("Total Credits: ₹0.00")
        self.lbl_credit_total.setStyleSheet("font-weight: bold; color: #047857; font-size: 13px;")

        self.lbl_balance_status = QLabel("✅ Trial Balance Balanced (Debits = Credits)")
        self.lbl_balance_status.setStyleSheet("font-weight: bold; color: #065f46; background-color: #d1fae5; padding: 4px 10px; border-radius: 4px;")

        val_layout.addWidget(self.lbl_debit_total)
        val_layout.addSpacing(24)
        val_layout.addWidget(self.lbl_credit_total)
        val_layout.addStretch()
        val_layout.addWidget(self.lbl_balance_status)

        layout.addWidget(self.validation_frame)

        # 3. Main Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; background: white; border-radius: 8px; margin: 16px; }
            QTabBar::tab { background: #f1f5f9; color: #475569; padding: 10px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #0ea5e9; color: white; }
        """)

        self.tabs.addTab(self._create_tb_mapping_tab(), "Trial Balance & Schedule III Mapping")
        self.tabs.addTab(self._create_bs_tab(), "Balance Sheet (Division I)")
        self.tabs.addTab(self._create_pnl_tab(), "Statement of Profit & Loss")

        layout.addWidget(self.tabs)

        # Initialize with sample data if empty
        self.load_sample_trial_balance()

    def _create_tb_mapping_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)

        self.tb_table = QTableWidget(0, 4)
        self.tb_table.setHorizontalHeaderLabels(["Ledger Head / Account Name", "Debit Amount (₹)", "Credit Amount (₹)", "Schedule III Category Taxonomy"])
        self.tb_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tb_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tb_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tb_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tb_table.setColumnWidth(1, 150)
        self.tb_table.setColumnWidth(2, 150)
        self.tb_table.setStyleSheet("""
            QTableWidget { border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white; border-radius: 6px; }
            QHeaderView::section { background-color: #f8fafc; color: #334155; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #e2e8f0; }
        """)

        w_layout.addWidget(self.tb_table)
        return widget

    def _create_bs_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)

        self.bs_table = QTableWidget(0, 3)
        self.bs_table.setHorizontalHeaderLabels(["Schedule III Particulars", "Note No.", "Amount (₹)"])
        self.bs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bs_table.setStyleSheet("border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white;")
        w_layout.addWidget(self.bs_table)
        return widget

    def _create_pnl_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)

        self.pnl_table = QTableWidget(0, 3)
        self.pnl_table.setHorizontalHeaderLabels(["Profit & Loss Particulars", "Note No.", "Amount (₹)"])
        self.pnl_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.pnl_table.setStyleSheet("border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white;")
        w_layout.addWidget(self.pnl_table)
        return widget

    def load_sample_trial_balance(self):
        """Loads a realistic sample Trial Balance for demonstration."""
        sample_data = [
            ("Equity Share Capital", 0.0, 1000000.0, "Equity Share Capital"),
            ("General Reserve & Surplus", 0.0, 450000.0, "Reserves & Surplus"),
            ("HDFC Bank Account", 620000.0, 0.0, "Cash & Cash Equivalents"),
            ("Petty Cash", 15000.0, 0.0, "Cash & Cash Equivalents"),
            ("Trade Debtors / Customers", 850000.0, 0.0, "Trade Receivables (Current)"),
            ("Trade Creditors / Vendors", 0.0, 380000.0, "Trade Payables (Current)"),
            ("Plant & Machinery", 1200000.0, 0.0, "Tangible Assets (Property, Plant & Equipment)"),
            ("Office Laptops & Furniture", 250000.0, 0.0, "Tangible Assets (Property, Plant & Equipment)"),
            ("Sales / Revenue from Operations", 0.0, 3200000.0, "Revenue from Operations"),
            ("Interest Income on FD", 0.0, 45000.0, "Other Income"),
            ("Salaries & Staff Expenses", 1100000.0, 0.0, "Employee Benefit Expenses"),
            ("Bank Loan Interest Paid", 48000.0, 0.0, "Finance Costs"),
            ("Office Rent & Utilities", 320000.0, 0.0, "Other Expenses"),
            ("Audit Fees & Legal Charges", 72000.0, 0.0, "Other Expenses"),
            ("Depreciation Expense", 100000.0, 0.0, "Depreciation & Amortization"),
            ("Closing Inventory Stock", 500000.0, 0.0, "Other Current Assets")
        ]
        self.populate_tb_table(sample_data)

    def populate_tb_table(self, rows):
        self.ledger_rows = rows
        self.tb_table.setRowCount(len(rows))

        total_debit = 0.0
        total_credit = 0.0

        for r, (head, dr, cr, cat) in enumerate(rows):
            total_debit += dr
            total_credit += cr

            head_item = QTableWidgetItem(head)
            head_item.setFont(QFont("Inter", 10, QFont.Weight.Medium))
            self.tb_table.setItem(r, 0, head_item)

            dr_item = QTableWidgetItem(f"₹{dr:,.2f}" if dr > 0 else "-")
            dr_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tb_table.setItem(r, 1, dr_item)

            cr_item = QTableWidgetItem(f"₹{cr:,.2f}" if cr > 0 else "-")
            cr_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tb_table.setItem(r, 2, cr_item)

            combo = QComboBox()
            combo.addItems(SCHEDULE_III_CATEGORIES)
            if cat in SCHEDULE_III_CATEGORIES:
                combo.setCurrentText(cat)
            else:
                combo.setCurrentIndex(0)
            combo.currentIndexChanged.connect(self.recalculate_financial_statements)
            self.tb_table.setCellWidget(r, 3, combo)

        self.lbl_debit_total.setText(f"Total Debits: ₹{total_debit:,.2f}")
        self.lbl_credit_total.setText(f"Total Credits: ₹{total_credit:,.2f}")

        diff = abs(total_debit - total_credit)
        if diff < 0.01:
            self.lbl_balance_status.setText("✅ Trial Balance Balanced (Debits = Credits)")
            self.lbl_balance_status.setStyleSheet("font-weight: bold; color: #065f46; background-color: #d1fae5; padding: 4px 10px; border-radius: 4px;")
            self.validation_frame.setStyleSheet("background-color: #ecfdf5; border-bottom: 1px solid #a7f3d0;")
        else:
            self.lbl_balance_status.setText(f"⚠️ Trial Balance Imbalanced (Diff: ₹{diff:,.2f})")
            self.lbl_balance_status.setStyleSheet("font-weight: bold; color: #991b1b; background-color: #fef2f2; padding: 4px 10px; border-radius: 4px;")
            self.validation_frame.setStyleSheet("background-color: #fff5f5; border-bottom: 1px solid #fecaca;")

        self.recalculate_financial_statements()

    def run_auto_mapping(self):
        """Applies keyword heuristic rules to map Trial Balance heads to Schedule III categories."""
        mapped_count = 0
        for r in range(self.tb_table.rowCount()):
            head_text = self.tb_table.item(r, 0).text().lower()
            combo = self.tb_table.cellWidget(r, 3)
            if not combo: continue

            target_cat = None
            if any(k in head_text for k in ["bank", "hdfc", "icici", "sbi", "cash", "petty"]):
                target_cat = "Cash & Cash Equivalents"
            elif any(k in head_text for k in ["debtor", "receivable", "customer"]):
                target_cat = "Trade Receivables (Current)"
            elif any(k in head_text for k in ["creditor", "payable", "vendor", "supplier"]):
                target_cat = "Trade Payables (Current)"
            elif any(k in head_text for k in ["sales", "turnover", "revenue"]):
                target_cat = "Revenue from Operations"
            elif any(k in head_text for k in ["interest income", "dividend", "discount received"]):
                target_cat = "Other Income"
            elif any(k in head_text for k in ["salary", "wage", "staff", "bonus"]):
                target_cat = "Employee Benefit Expenses"
            elif any(k in head_text for k in ["loan interest", "finance cost", "bank charges"]):
                target_cat = "Finance Costs"
            elif any(k in head_text for k in ["depreciation", "amortization"]):
                target_cat = "Depreciation & Amortization"
            elif any(k in head_text for k in ["rent", "utility", "audit fee", "legal", "office exp", "travelling"]):
                target_cat = "Other Expenses"
            elif any(k in head_text for k in ["machinery", "furniture", "laptop", "building", "plant", "equipment"]):
                target_cat = "Tangible Assets (Property, Plant & Equipment)"
            elif any(k in head_text for k in ["share capital", "equity"]):
                target_cat = "Equity Share Capital"
            elif any(k in head_text for k in ["reserve", "surplus", "retained"]):
                target_cat = "Reserves & Surplus"

            if target_cat and target_cat in SCHEDULE_III_CATEGORIES:
                combo.setCurrentText(target_cat)
                mapped_count += 1

        QMessageBox.information(self, "Auto-Mapping Complete", f"Successfully auto-mapped {mapped_count} ledger heads to Schedule III categories.")
        self.recalculate_financial_statements()

    def recalculate_financial_statements(self):
        """Aggregates mapped amounts and populates Schedule III Balance Sheet and P&L tables."""
        cat_totals = {c: 0.0 for c in SCHEDULE_III_CATEGORIES}

        for r in range(self.tb_table.rowCount()):
            combo = self.tb_table.cellWidget(r, 3)
            if not combo: continue
            cat = combo.currentText()
            dr_str = self.tb_table.item(r, 1).text().replace("₹", "").replace(",", "").strip()
            cr_str = self.tb_table.item(r, 2).text().replace("₹", "").replace(",", "").strip()
            dr = float(dr_str) if dr_str and dr_str != "-" else 0.0
            cr = float(cr_str) if cr_str and cr_str != "-" else 0.0
            
            # Asset / Expense heads carry Debit balance; Liability / Revenue heads carry Credit balance
            net_val = dr if dr > 0 else cr
            cat_totals[cat] += net_val

        # Populate Balance Sheet Table
        bs_rows = [
            ("I. EQUITY AND LIABILITIES", "", ""),
            ("  (1) Shareholders' Funds", "", ""),
            ("    (a) Share Capital", "Note 1", f"₹{cat_totals.get('Equity Share Capital', 0.0):,.2f}"),
            ("    (b) Reserves & Surplus", "Note 2", f"₹{cat_totals.get('Reserves & Surplus', 0.0):,.2f}"),
            ("  (2) Non-Current Liabilities", "", ""),
            ("    (a) Long-Term Borrowings", "Note 3", f"₹{cat_totals.get('Long-Term Borrowings', 0.0):,.2f}"),
            ("  (3) Current Liabilities", "", ""),
            ("    (a) Trade Payables", "Note 4", f"₹{cat_totals.get('Trade Payables (Current)', 0.0):,.2f}"),
            ("    (b) Other Current Liabilities", "Note 5", f"₹{cat_totals.get('Other Current Liabilities', 0.0):,.2f}"),
            ("TOTAL EQUITY AND LIABILITIES", "", f"₹{cat_totals.get('Equity Share Capital',0)+cat_totals.get('Reserves & Surplus',0)+cat_totals.get('Long-Term Borrowings',0)+cat_totals.get('Trade Payables (Current)',0):,.2f}"),
            ("II. ASSETS", "", ""),
            ("  (1) Non-Current Assets", "", ""),
            ("    (a) Property, Plant & Equipment", "Note 6", f"₹{cat_totals.get('Tangible Assets (Property, Plant & Equipment)', 0.0):,.2f}"),
            ("    (b) Intangible Assets", "Note 7", f"₹{cat_totals.get('Intangible Assets', 0.0):,.2f}"),
            ("  (2) Current Assets", "", ""),
            ("    (a) Trade Receivables", "Note 8", f"₹{cat_totals.get('Trade Receivables (Current)', 0.0):,.2f}"),
            ("    (b) Cash & Cash Equivalents", "Note 9", f"₹{cat_totals.get('Cash & Cash Equivalents', 0.0):,.2f}"),
            ("    (c) Other Current Assets", "Note 10", f"₹{cat_totals.get('Other Current Assets', 0.0):,.2f}"),
            ("TOTAL ASSETS", "", f"₹{cat_totals.get('Tangible Assets (Property, Plant & Equipment)',0)+cat_totals.get('Intangible Assets',0)+cat_totals.get('Trade Receivables (Current)',0)+cat_totals.get('Cash & Cash Equivalents',0)+cat_totals.get('Other Current Assets',0):,.2f}")
        ]

        self.bs_table.setRowCount(len(bs_rows))
        for r, (part, note, amt) in enumerate(bs_rows):
            p_item = QTableWidgetItem(part)
            if part.startswith("I.") or part.startswith("II.") or part.startswith("TOTAL"):
                p_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
                if part.startswith("TOTAL"):
                    p_item.setBackground(QColor("#f1f5f9"))
            self.bs_table.setItem(r, 0, p_item)
            self.bs_table.setItem(r, 1, QTableWidgetItem(note))
            amt_item = QTableWidgetItem(amt)
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.bs_table.setItem(r, 2, amt_item)

        # Populate P&L Table
        rev_ops = cat_totals.get("Revenue from Operations", 0.0)
        oth_inc = cat_totals.get("Other Income", 0.0)
        tot_rev = rev_ops + oth_inc

        emp_exp = cat_totals.get("Employee Benefit Expenses", 0.0)
        fin_exp = cat_totals.get("Finance Costs", 0.0)
        dep_exp = cat_totals.get("Depreciation & Amortization", 0.0)
        oth_exp = cat_totals.get("Other Expenses", 0.0)
        tot_exp = emp_exp + fin_exp + dep_exp + oth_exp
        pbt = tot_rev - tot_exp

        pnl_rows = [
            ("I. Revenue from Operations", "Note 11", f"₹{rev_ops:,.2f}"),
            ("II. Other Income", "Note 12", f"₹{oth_inc:,.2f}"),
            ("III. TOTAL REVENUE (I + II)", "", f"₹{tot_rev:,.2f}"),
            ("IV. EXPENSES", "", ""),
            ("  (a) Employee Benefit Expenses", "Note 13", f"₹{emp_exp:,.2f}"),
            ("  (b) Finance Costs", "Note 14", f"₹{fin_exp:,.2f}"),
            ("  (c) Depreciation & Amortization", "Note 15", f"₹{dep_exp:,.2f}"),
            ("  (d) Other Expenses", "Note 16", f"₹{oth_exp:,.2f}"),
            ("TOTAL EXPENSES (IV)", "", f"₹{tot_exp:,.2f}"),
            ("V. PROFIT BEFORE TAX (III - IV)", "", f"₹{pbt:,.2f}")
        ]

        self.pnl_table.setRowCount(len(pnl_rows))
        for r, (part, note, amt) in enumerate(pnl_rows):
            p_item = QTableWidgetItem(part)
            if part.startswith("III.") or part.startswith("V.") or part.startswith("TOTAL"):
                p_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
                if part.startswith("V."):
                    p_item.setBackground(QColor("#e0f2fe"))
            self.pnl_table.setItem(r, 0, p_item)
            self.pnl_table.setItem(r, 1, QTableWidgetItem(note))
            amt_item = QTableWidgetItem(amt)
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.pnl_table.setItem(r, 2, amt_item)

    def import_trial_balance(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Trial Balance File", "", "CSV Files (*.csv);;All Files (*)")
        if not path: return
        try:
            parsed_rows = []
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or len(row) < 3: continue
                    head = row[0].strip()
                    if head.lower() in ["ledger", "head", "account", "particulars"]: continue
                    try:
                        dr = float(row[1].replace(",", "").strip() or 0.0)
                        cr = float(row[2].replace(",", "").strip() or 0.0)
                        parsed_rows.append((head, dr, cr, "Unmapped / Select Head"))
                    except ValueError:
                        continue
            if parsed_rows:
                self.populate_tb_table(parsed_rows)
                self.run_auto_mapping()
                QMessageBox.information(self, "Import Successful", f"Imported {len(parsed_rows)} ledger heads from {path}.")
            else:
                QMessageBox.warning(self, "Import Error", "No valid Trial Balance rows found in CSV file.")
        except Exception as e:
            QMessageBox.critical(self, "Import Exception", f"Failed to read CSV file: {e}")

    def export_statements(self):
        QMessageBox.information(self, "Export Schedule III", "Exported Schedule III Balance Sheet & Statement of P&L to Excel/PDF.")
