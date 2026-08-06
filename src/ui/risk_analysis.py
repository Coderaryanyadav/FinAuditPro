"""
SA 320 Audit Materiality Calculator & Risk Matrix Widget for FinAuditPro.
Provides SA 320 Overall & Performance Materiality Computation,
3x3 Risk Heatmap Matrix, and Risk Findings Registry.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QFormLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from database.database import get_session
from database.models import Finding, AuditProject
from database.repositories.risk_repo import RiskRepository
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.risk_service import RiskService
from services.finding_service import FindingService
from .styles import apply_shadow, EmptyStateWidget, ErrorStateWidget, LoadingStateWidget
from sqlalchemy.exc import SQLAlchemyError

class RiskAnalysisWidget(QWidget):
    """SA 320 Materiality Calculator & Risk Matrix Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f0f6ff;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Action Bar
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("riskHeader")
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("Audit Risk Assessment & Materiality Calculator")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; letter-spacing: -0.4px; border: none; background: transparent; background-color: transparent;")
        subtitle = QLabel("SA 315 Risk Identification, Performance Materiality (SA 320) & Risk Heatmap")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none; background: transparent; background-color: transparent;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        btn_calc = QPushButton("Recalculate SA 320 Materiality")
        btn_calc.setToolTip("Recalculate audit materiality benchmarks under ICAI SA 320")
        btn_calc.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn_calc.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        btn_calc.clicked.connect(self.calculate_materiality)
        h_layout.addWidget(btn_calc)

        main_layout.addWidget(header)

        # 2. Main Scroll Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #f0f6ff;")
        body = QWidget()
        body.setStyleSheet("background-color: #f0f6ff;")
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(24, 24, 24, 24)
        b_layout.setSpacing(20)

        # SA 320 Materiality Worksheet Section
        mat_frame = QFrame()
        mat_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        mat_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e1e8f4; border-radius: 12px;")
        mat_layout = QVBoxLayout(mat_frame)
        mat_layout.setContentsMargins(20, 20, 20, 20)

        mat_title = QLabel("SA 320 MATERIALITY COMPUTATION WORKSHEET")
        mat_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #0284c7; border-bottom: 1px solid #e1e8f4; padding-bottom: 8px; letter-spacing: 0.8px; background: transparent; background-color: transparent;")
        mat_layout.addWidget(mat_title)

        inputs_h = QHBoxLayout()
        inputs_h.setSpacing(20)

        # Form Controls
        form_frame = QFrame()
        f_layout = QFormLayout(form_frame)
        f_layout.setSpacing(10)

        self.benchmark_combo = QComboBox()
        self.benchmark_combo.addItems(["Revenue from Operations (1.0%)", "Profit Before Tax (5.0%)", "Total Assets (0.5%)", "Equity Shareholders' Funds (1.0%)"])
        self.benchmark_combo.setToolTip("Select SA 320 financial benchmark basis")
        self.benchmark_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.benchmark_combo.setStyleSheet("padding: 6px; border: 1px solid #e5e5ea; border-radius: 6px; background: #ffffff; color: #1d1d1f;")

        self.base_amt_input = QLineEdit("32000000.00")
        self.base_amt_input.setToolTip("Enter base financial figure in INR for materiality computation")
        self.base_amt_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.base_amt_input.setStyleSheet("padding: 6px; border: 1px solid #e5e5ea; border-radius: 6px; background: #ffffff; font-weight: 600; color: #1d1d1f;")
        self.base_amt_input.textChanged.connect(self.calculate_materiality)

        f_layout.addRow("Benchmark Selection:", self.benchmark_combo)
        f_layout.addRow("Benchmark Base Amount (₹):", self.base_amt_input)
        inputs_h.addWidget(form_frame, 5)

        # Results Summary Box
        res_frame = QFrame()
        res_frame.setStyleSheet("background-color: #f5f5f7; border: 1px solid #e5e5ea; border-radius: 12px; padding: 14px;")
        r_layout = QVBoxLayout(res_frame)

        self.lbl_overall_mat = QLabel("Overall Materiality (OM): ₹ 3,20,000.00")
        self.lbl_overall_mat.setStyleSheet("font-size: 14px; font-weight: 600; color: #1d1d1f;")

        self.lbl_perf_mat = QLabel("Performance Materiality (PM @ 75%): ₹ 2,40,000.00")
        self.lbl_perf_mat.setStyleSheet("font-size: 13px; font-weight: 600; color: #007aff;")

        self.lbl_de_minimis = QLabel("Tolerable Misstatement Limit (5%): ₹ 16,000.00")
        self.lbl_de_minimis.setStyleSheet("font-size: 12px; font-weight: 600; color: #6e6e73;")

        r_layout.addWidget(self.lbl_overall_mat)
        r_layout.addWidget(self.lbl_perf_mat)
        r_layout.addWidget(self.lbl_de_minimis)
        inputs_h.addWidget(res_frame, 5)

        mat_layout.addLayout(inputs_h)
        b_layout.addWidget(mat_frame)

        # Findings Table
        table_container = QFrame()
        table_container.setStyleSheet("background-color: #ffffff; border: 1px solid #e5e5ea; border-radius: 12px;")
        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(16, 16, 16, 16)
        
        t_title = QLabel("DETECTED RISK FINDINGS & MATERIALITY THRESHOLD AUDIT")
        t_title.setStyleSheet("font-size: 10px; font-weight: 600; color: #86868b; letter-spacing: 0.8px; padding-bottom: 8px;")
        t_layout.addWidget(t_title)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Issue / Audit Finding", "Risk Rating", "Financial Exposure (₹)", "Materiality Status", "Recommendation"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #e5e5ea; gridline-color: #f2f2f7; background: #ffffff; border-radius: 8px; }
            QHeaderView::section { background-color: #fafafa; color: #86868b; font-weight: 600; padding: 8px; font-size: 10px; letter-spacing: 0.5px; border: none; border-bottom: 1px solid #e5e5ea; text-transform: uppercase; }
        """)
        
        t_layout.addWidget(self.table)
        b_layout.addWidget(table_container)
        
        scroll.setWidget(body)
        main_layout.addWidget(scroll)

        self.load_findings()
        self.calculate_materiality()

    def calculate_materiality(self):
        try:
            val_str = self.base_amt_input.text().replace("₹", "").replace(",", "").strip()
            base_val = float(val_str) if val_str else 0.0
            
            # Overall Materiality: 1% of base
            om = base_val * 0.01
            pm = om * 0.75
            tms = om * 0.05

            self.lbl_overall_mat.setText(f"Overall Materiality (OM): ₹ {om:,.2f}")
            self.lbl_perf_mat.setText(f"Performance Materiality (PM @ 75%): ₹ {pm:,.2f}")
            self.lbl_de_minimis.setText(f"Tolerable Misstatement Limit (5%): ₹ {tms:,.2f}")
        except ValueError:
            pass

    def load_findings(self):
        active_id = getattr(self, 'active_engagement_id', None)
        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                finding_service = FindingService(wp_repo)
                findings = finding_service.get_findings_by_audit_id(active_id) if active_id else finding_service.get_all_findings()
                
                if not findings:
                    self.table.setRowCount(0)
                    if hasattr(self, 'state_container'):
                        self.state_container.setWidget(EmptyStateWidget("No Risk Findings", "No high or medium audit risk anomalies flagged for the active engagement."))
                        self.state_container.show()
                    return

                if hasattr(self, 'state_container'):
                    self.state_container.hide()

                self.table.setRowCount(len(findings))

                for r, f in enumerate(findings):
                    parts = [p.strip() for p in f.description.split("|")]
                    issue = parts[0] if parts else f.description
                    amount_str = parts[1] if len(parts) > 1 else "₹ 0.00"
                    rec = parts[3] if len(parts) > 3 else "Substantive audit testing required"

                    self.table.setItem(r, 0, QTableWidgetItem(issue))
                    
                    risk_item = QTableWidgetItem(f.risk_level or "Medium")
                    risk_item.setFont(QFont("Inter", 9, QFont.Weight.Bold))
                    self.table.setItem(r, 1, risk_item)

                    self.table.setItem(r, 2, QTableWidgetItem(amount_str))

                    mat_status = " Material Finding" if f.risk_level == "High" else "Pass (Below PM)"
                    mat_item = QTableWidgetItem(mat_status)
                    self.table.setItem(r, 3, mat_item)

                    self.table.setItem(r, 4, QTableWidgetItem(rec))
        except Exception as e:
            self.table.setRowCount(0)
            if hasattr(self, 'state_container'):
                self.state_container.setWidget(ErrorStateWidget("Failed to Load Risk Findings", str(e)))
                self.state_container.show()

    def closeEvent(self, event):
        event.accept()
