"""
GST Reconciliation & ITC Verification Workspace View for FinAuditPro.
Compare purchase register entries against GSTR-2B and audit statutory ITC claims.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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

from finauditpro.domain.entities import Engagement

SAMPLE_GST_INVOICES = [
    ("INV-2025-0891", "2025-11-12", "Apex Industrial Supplies Ltd", "27AAACA1234A1Z5", 450000.0, 81000.0, 81000.0, 0.0, "Matched", "✓ Matched"),
    ("INV-2025-0904", "2025-11-15", "Bharat Logistics Solutions", "27AABCB5678B1Z2", 280000.0, 50400.0, 0.0, -50400.0, "Missing in 2B", "! Missing in 2B"),
    ("INV-2025-0922", "2025-11-20", "Crestwood IT Consultancy", "27AACCC9012C1Z8", 180000.0, 32400.0, 28800.0, -3600.0, "Rate Mismatch", "! Rate Mismatch"),
    ("INV-2025-0955", "2025-11-25", "Delta Fleet Rentals (Motor Vehicles)", "27AABCD3456D1Z1", 350000.0, 63000.0, 63000.0, 0.0, "Ineligible ITC", "⚠️ Ineligible Sec 17(5)"),
    ("INV-2025-0988", "2025-12-02", "Everest Office Infrastructure", "27AAACE7890E1Z4", 620000.0, 111600.0, 111600.0, 0.0, "Matched", "✓ Matched"),
    ("INV-2025-1012", "2025-12-08", "Falcon Packaging Works", "27AACFF1234F1Z7", 210000.0, 37800.0, 37800.0, 0.0, "Matched", "✓ Matched"),
    ("INV-2025-1045", "2025-12-14", "Global Steel Fabrication", "27AACGG5678G1Z0", 890000.0, 160200.0, 0.0, -160200.0, "Missing in 2B", "! Missing in 2B"),
    ("INV-2025-1080", "2025-12-19", "Horizon Tech Solutions", "27AAACH9012H1Z3", 310000.0, 55800.0, 55800.0, 0.0, "Matched", "✓ Matched"),
]


class GSTVerificationView(QWidget):
    """Enterprise GST Reconciliation & ITC Verification Workspace Widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_engagement: Engagement | None = None
        self._init_ui()

    def set_active_engagement(self, engagement: Engagement | None) -> None:
        self.current_engagement = engagement
        self.load_data()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("GST Reconciliation Workspace")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; border: none;")
        subtitle = QLabel("Compare purchase register entries against GSTR-2B and audit statutory ITC claims.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        btn_run_recon = QPushButton("⚡ Run GST Matching")
        btn_run_recon.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run_recon.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: #ffffff;
                font-size: 12px; font-weight: 700;
                border-radius: 6px; padding: 7px 16px; border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        btn_run_recon.clicked.connect(self.load_data)
        h_layout.addWidget(btn_run_recon)

        main_layout.addWidget(header)

        # 2. Metric Strip
        strip = QFrame()
        strip.setFixedHeight(54)
        strip.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        s_layout = QHBoxLayout(strip)
        s_layout.setContentsMargins(24, 0, 24, 0)
        s_layout.setSpacing(16)

        self.lbl_total_inv = self._create_metric_badge("TOTAL INVOICES", "8", "#0284c7", "#e0f2fe")
        self.lbl_matched = self._create_metric_badge("MATCHED", "5", "#047857", "#dcfce7")
        self.lbl_mismatched = self._create_metric_badge("MISMATCHED / MISSING", "3", "#dc2626", "#fee2e2")
        self.lbl_ineligible = self._create_metric_badge("INELIGIBLE SEC 17(5)", "1", "#d97706", "#fef3c7")

        for b in [self.lbl_total_inv, self.lbl_matched, self.lbl_mismatched, self.lbl_ineligible]:
            s_layout.addWidget(b)
        s_layout.addStretch()
        main_layout.addWidget(strip)

        # 3. Table View
        table_container = QFrame()
        table_container.setStyleSheet("background-color: #ffffff; padding: 16px;")
        tc_layout = QVBoxLayout(table_container)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Invoice No", "Date", "Vendor Name", "GSTIN", "Taxable Amt (₹)", "Books ITC (₹)", "2B ITC (₹)", "Variance (₹)", "Recon Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #ffffff; border: 1px solid #e1e8f4; border-radius: 8px; font-size: 12px; color: #0f172a; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: 700; font-size: 11px; padding: 8px; border: none; }
        """)
        tc_layout.addWidget(self.table)

        main_layout.addWidget(table_container, 1)
        self.load_data()

    def _create_metric_badge(self, title: str, val: str, fg: str, bg: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"background-color: {bg}; border-radius: 6px; padding: 4px 12px;")
        l = QHBoxLayout(f)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8)

        t = QLabel(title)
        t.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {fg};")
        v = QLabel(val)
        v.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {fg};")
        l.addWidget(t)
        l.addWidget(v)
        return f

    def load_data(self) -> None:
        self.table.setRowCount(0)
        for idx, row in enumerate(SAMPLE_GST_INVOICES):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(row[0]))
            self.table.setItem(idx, 1, QTableWidgetItem(row[1]))
            self.table.setItem(idx, 2, QTableWidgetItem(row[2]))
            self.table.setItem(idx, 3, QTableWidgetItem(row[3]))
            self.table.setItem(idx, 4, QTableWidgetItem(f"₹{row[4]:,.2f}"))
            self.table.setItem(idx, 5, QTableWidgetItem(f"₹{row[5]:,.2f}"))
            self.table.setItem(idx, 6, QTableWidgetItem(f"₹{row[6]:,.2f}"))
            self.table.setItem(idx, 7, QTableWidgetItem(f"₹{row[7]:,.2f}"))
            self.table.setItem(idx, 8, QTableWidgetItem(row[9]))
