"""
Financial Statements Verification Widget for FinAuditPro.
Renders Balance Sheet, Profit & Loss Statement, and Cash Flow ledgers.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget)
from PySide6.QtCore import Qt

class FinancialStatementsWidget(QWidget):
    """Renders financial statement ledger tables for audit verification."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("Financial Statements Inspection")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        layout.addWidget(header)

        # Tab Widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; background: white; border-radius: 8px; margin: 16px; }
            QTabBar::tab { background: #f1f5f9; color: #475569; padding: 10px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #0ea5e9; color: white; }
        """)

        tabs.addTab(self._create_statement_table("Balance Sheet"), "Balance Sheet")
        tabs.addTab(self._create_statement_table("Statement of Profit & Loss"), "Statement of P&L")
        tabs.addTab(self._create_statement_table("Cash Flow Statement"), "Cash Flows")

        layout.addWidget(tabs)

    def _create_statement_table(self, statement_name: str) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Line Item / Head", "Note Ref", "FY 2025-26 (Current)", "FY 2024-25 (Prior)"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setStyleSheet("border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white;")

        try:
            from database.database import SessionLocal
            from database.models import Document
            session = SessionLocal()
            docs = session.query(Document).all()
            session.close()
            table.setRowCount(0)
        except Exception:
            table.setRowCount(0)

        w_layout.addWidget(table)
        return widget
