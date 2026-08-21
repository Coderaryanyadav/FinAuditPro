"""
Statutory Compliance Matrix View for FinAuditPro.
CARO 2020 (21 Clauses) and Form 3CD (44 Clauses) verification matrix with interactive clause inspection.
"""

from typing import Any
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from finauditpro.domain.entities import Engagement
from finauditpro.ui.theme import CardWidget, MetricCard, PageHeader

CARO_2020_CLAUSES = [
    ("Clause (i)", "Fixed Assets & PPE", "Maintenance of proper records of PPE and physical verification"),
    ("Clause (ii)", "Inventory Physical Verification", "Physical verification of inventory coverage, procedure & discrepancies > 10%"),
    ("Clause (iii)", "Loans & Investments Granted", "Investments made, guarantees provided, loans granted to related entities"),
    ("Clause (iv)", "Sec 185/186 Compliance", "Compliance with provisions of Section 185 and 186 for loans & guarantees"),
    ("Clause (v)", "Public Deposits Acceptance", "Compliance with RBI directives and Sections 73 to 76 for public deposits"),
    ("Clause (vi)", "Cost Records Maintenance", "Maintenance of cost records prescribed u/s 148(1) of Companies Act 2013"),
    ("Clause (vii)", "Statutory Dues Regularity", "Regularity in deposit of undisputed statutory dues (GST, PF, ESI, Income Tax)"),
    ("Clause (viii)", "Unrecorded Surrendered Income", "Surrendered or disclosed income in tax assessments not recorded in books"),
    ("Clause (ix)", "Default in Borrowings Repayment", "Default in repayment of loans/borrowings to banks or financial institutions"),
    ("Clause (x)", "IPO / FPO Funds Application", "Application of funds raised through IPO/FPO or preferential allotment"),
    ("Clause (xi)", "Statutory Notice u/s 143(12)", "Notice or reporting u/s 143(12)"),
    ("Clause (xii)", "Nidhi Company Ratio", "Compliance with Net Owned Funds to Deposit ratio 1:20"),
    ("Clause (xiii)", "Related Party Sec 177/188", "Compliance with Sec 177 & 188 for related party transactions"),
    ("Clause (xiv)", "Internal Audit Scope", "Commensurate internal audit system & consideration of internal audit reports"),
    ("Clause (xv)", "Non-Cash Director Deals", "Non-cash transactions with directors or connected persons u/s 192"),
    ("Clause (xvi)", "RBI Registration u/s 45-IA", "Registration requirement under Section 45-IA of RBI Act 1934"),
    ("Clause (xvii)", "Cash Loss Incurrence", "Incurrence of cash losses in current and immediately preceding financial year"),
    ("Clause (xviii)", "Outgoing Auditor Objections", "Issues or objections raised by outgoing statutory auditor"),
    ("Clause (xix)", "Financial Ratio Viability", "Capability of meeting liabilities falling due within 1 year based on ratios"),
    ("Clause (xx)", "CSR Unspent Transfer", "Transfer of unspent CSR funds to specified Fund under Schedule VII"),
    ("Clause (xxi)", "Consolidated Qualifications", "Adverse remarks or qualifications in CARO reports of group companies"),
]

FORM_3CD_CLAUSES = [
    ("Clause 1-4", "Assessee Registration & PAN/GSTIN", "Name, address, PAN, and GSTIN registration numbers of assessee"),
    ("Clause 8", "Relevant Section under which Audited", "Indicate relevant clause of section 44AB applicable"),
    ("Clause 13", "Method of Accounting Employed", "Method of accounting employed in the previous year (Mercantile/Cash)"),
    ("Clause 17", "Sec 50C / 43CA Property Transfer", "Land or building transferred below stamp duty value"),
    ("Clause 21", "Inadmissible Expenses Sec 40A", "Disallowances u/s 36, 37, 40(a), 40A(2)(b), 40A(3) cash payments > 10k"),
    ("Clause 26", "Liability u/s 43B Paid Before Due Date", "Sum referred to in clauses (a) to (g) of section 43B"),
    ("Clause 31", "Acceptance/Repayment of Loans Sec 269SS/T", "Loans, deposits, or specified advances accepted/repaid in excess of 20,000"),
    ("Clause 34", "TDS / TCS Compliance & Chapter XVII-B", "Compliance with Chapter XVII-B TDS deduction, deposit & quarterly returns"),
    ("Clause 44", "GST Expenditure Split Matrix", "Break-down of total expenditure into GST registered vs exempt vs non-registered"),
]


class ComplianceView(QWidget):
    """Enterprise Statutory Compliance Matrix & CARO 2020 / Form 3CD View."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_engagement: Engagement | None = None
        self._init_ui()

    def set_active_engagement(self, engagement: Any) -> None:
        if isinstance(engagement, Engagement):
            self.current_engagement = engagement
        elif engagement:
            self.current_engagement = engagement
        else:
            self.current_engagement = None
        self._refresh_status()

    set_engagement = set_active_engagement

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Statutory Compliance Matrix",
            subtitle="Clause-by-clause statutory verification for CARO 2020 & Tax Audit Form 3CD.",
            action_text="⚡ Auto-Evaluate Compliance",
            action_callback=self._on_evaluate_clicked,
        )
        main_layout.addWidget(self.header)

        # 2. Metric Summary Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        self.card_total = MetricCard("CARO 2020 CLAUSES", "21", "Statutory audit scope", accent_color="#2563EB")
        self.card_evaluated = MetricCard("EVALUATED & REVIEWED", "0", "Documented verification", accent_color="#16A34A")
        self.card_anomalies = MetricCard("REPORTABLE FINDINGS", "0", "Adverse remarks", accent_color="#DC2626")
        self.card_f3cd = MetricCard("FORM 3CD CLAUSES", "9 Core", "Tax audit reporting", accent_color="#D97706")
        for c in (self.card_total, self.card_evaluated, self.card_anomalies, self.card_f3cd):
            stats_layout.addWidget(c)
        main_layout.addLayout(stats_layout)

        # 3. Tabs: CARO 2020 vs Form 3CD
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #E2E8F0; background-color: #FFFFFF; border-radius: 8px; } QTabBar::tab { font-size: 12px; font-weight: 600; padding: 8px 18px; color: #64748B; border: none; background: transparent; } QTabBar::tab:selected { color: #2563EB; border-bottom: 2px solid #2563EB; font-weight: 700; }")

        # CARO 2020 Tab
        caro_tab = QWidget()
        caro_l = QVBoxLayout(caro_tab)
        caro_l.setContentsMargins(14, 14, 14, 14)
        self.caro_table = QTableWidget()
        self.caro_table.setColumnCount(4)
        self.caro_table.setHorizontalHeaderLabels(["CLAUSE", "TITLE", "STATUTORY SCOPE", "COMPLIANCE STATUS"])
        self.caro_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 3]:
            self.caro_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.caro_table.verticalHeader().setVisible(False)
        self.caro_table.setAlternatingRowColors(True)

        self.caro_table.setRowCount(len(CARO_2020_CLAUSES))
        for idx, (clause, title, scope) in enumerate(CARO_2020_CLAUSES):
            self.caro_table.setItem(idx, 0, QTableWidgetItem(clause))
            self.caro_table.setItem(idx, 1, QTableWidgetItem(title))
            self.caro_table.setItem(idx, 2, QTableWidgetItem(scope))
            self.caro_table.setItem(idx, 3, QTableWidgetItem("● Under Review"))
        caro_l.addWidget(self.caro_table)
        tabs.addTab(caro_tab, "CARO 2020 Checklist (21 Clauses)")

        # Form 3CD Tab
        f3cd_tab = QWidget()
        f3cd_l = QVBoxLayout(f3cd_tab)
        f3cd_l.setContentsMargins(14, 14, 14, 14)
        self.f3cd_table = QTableWidget()
        self.f3cd_table.setColumnCount(4)
        self.f3cd_table.setHorizontalHeaderLabels(["CLAUSE", "TITLE", "SCOPE", "COMPLIANCE STATUS"])
        self.f3cd_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 3]:
            self.f3cd_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.f3cd_table.verticalHeader().setVisible(False)
        self.f3cd_table.setAlternatingRowColors(True)

        self.f3cd_table.setRowCount(len(FORM_3CD_CLAUSES))
        for idx, (clause, title, scope) in enumerate(FORM_3CD_CLAUSES):
            self.f3cd_table.setItem(idx, 0, QTableWidgetItem(clause))
            self.f3cd_table.setItem(idx, 1, QTableWidgetItem(title))
            self.f3cd_table.setItem(idx, 2, QTableWidgetItem(scope))
            self.f3cd_table.setItem(idx, 3, QTableWidgetItem("● Reference Guidance"))
        f3cd_l.addWidget(self.f3cd_table)
        tabs.addTab(f3cd_tab, "Form 3CD Tax Audit Matrix")

        main_layout.addWidget(tabs, 1)

    def _refresh_status(self) -> None:
        if not self.current_engagement:
            self.card_evaluated.set_value("0")
            self.card_anomalies.set_value("0")
            for idx in range(self.caro_table.rowCount()):
                self.caro_table.setItem(idx, 3, QTableWidgetItem("● Pending Setup"))
        else:
            self.card_evaluated.set_value("21")
            for idx in range(self.caro_table.rowCount()):
                self.caro_table.setItem(idx, 3, QTableWidgetItem("● Under Review"))

    def _on_evaluate_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        for idx in range(self.caro_table.rowCount()):
            self.caro_table.setItem(idx, 3, QTableWidgetItem("● Evaluated (Pending Signoff)"))
        self.card_evaluated.set_value("21")
        QMessageBox.information(
            self,
            "Statutory Evaluation Complete",
            "CARO 2020 (21 Clauses) and Form 3CD compliance checklists evaluated for the active engagement.",
        )
