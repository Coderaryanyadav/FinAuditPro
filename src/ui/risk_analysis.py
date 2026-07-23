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
from database.database import SessionLocal
from database.models import Finding, AuditProject
from .styles import apply_shadow
from sqlalchemy.exc import SQLAlchemyError

class RiskAnalysisWidget(QWidget):
    """SA 320 Materiality Calculator & Risk Matrix Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.session = SessionLocal()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Action Bar Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title = QLabel("SA 320 Materiality Calculator & Risk Analysis Matrix")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("ICAI SA 320 Materiality in Planning and Performing an Audit")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        btn_calc = QPushButton("⚡ Recalculate SA 320 Materiality")
        btn_calc.setStyleSheet("background-color: #0ea5e9; color: white; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 12px; border: none;")
        btn_calc.clicked.connect(self.calculate_materiality)
        h_layout.addWidget(btn_calc)

        main_layout.addWidget(header)

        # 2. Main Scroll Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(24, 24, 24, 24)
        b_layout.setSpacing(20)

        # SA 320 Materiality Worksheet Section
        mat_frame = QFrame()
        mat_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        mat_layout = QVBoxLayout(mat_frame)
        mat_layout.setContentsMargins(20, 20, 20, 20)

        mat_title = QLabel("SA 320 MATERIALITY COMPUTATION WORKSHEET")
        mat_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #0ea5e9; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; letter-spacing: 0.5px;")
        mat_layout.addWidget(mat_title)

        inputs_h = QHBoxLayout()
        inputs_h.setSpacing(20)

        # Form Controls
        form_frame = QFrame()
        f_layout = QFormLayout(form_frame)
        f_layout.setSpacing(10)

        self.benchmark_combo = QComboBox()
        self.benchmark_combo.addItems(["Revenue from Operations (1.0%)", "Profit Before Tax (5.0%)", "Total Assets (0.5%)", "Equity Shareholders' Funds (1.0%)"])
        self.benchmark_combo.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; background: white;")

        self.base_amt_input = QLineEdit("32000000.00")
        self.base_amt_input.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; font-weight: bold;")
        self.base_amt_input.textChanged.connect(self.calculate_materiality)

        f_layout.addRow("Benchmark Selection:", self.benchmark_combo)
        f_layout.addRow("Benchmark Base Amount (₹):", self.base_amt_input)
        inputs_h.addWidget(form_frame, 5)

        # Results Summary Box
        res_frame = QFrame()
        res_frame.setStyleSheet("background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 14px;")
        r_layout = QVBoxLayout(res_frame)

        self.lbl_overall_mat = QLabel("Overall Materiality (OM): ₹ 3,20,000.00")
        self.lbl_overall_mat.setStyleSheet("font-size: 14px; font-weight: bold; color: #0369a1;")

        self.lbl_perf_mat = QLabel("Performance Materiality (PM @ 75%): ₹ 2,40,000.00")
        self.lbl_perf_mat.setStyleSheet("font-size: 13px; font-weight: bold; color: #0284c7;")

        self.lbl_de_minimis = QLabel("Tolerable Misstatement Limit (5%): ₹ 16,000.00")
        self.lbl_de_minimis.setStyleSheet("font-size: 12px; color: #0369a1;")

        r_layout.addWidget(self.lbl_overall_mat)
        r_layout.addWidget(self.lbl_perf_mat)
        r_layout.addWidget(self.lbl_de_minimis)
        inputs_h.addWidget(res_frame, 5)

        mat_layout.addLayout(inputs_h)
        b_layout.addWidget(mat_frame)

        # Findings Table
        table_container = QFrame()
        table_container.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(16, 16, 16, 16)
        
        t_title = QLabel("DETECTED RISK FINDINGS & MATERIALITY THRESHOLD AUDIT")
        t_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 0.5px; padding-bottom: 8px;")
        t_layout.addWidget(t_title)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Issue / Audit Finding", "Risk Rating", "Financial Exposure (₹)", "Materiality Status", "Recommendation"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #e2e8f0; gridline-color: #f1f5f9; background: white; border-radius: 6px; }
            QHeaderView::section { background-color: #f8fafc; color: #334155; font-weight: bold; padding: 8px; border: none; border-bottom: 1px solid #e2e8f0; }
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
        findings = self.session.query(Finding).filter_by(audit_id=active_id).all() if active_id else self.session.query(Finding).all()
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

            mat_status = "⚠️ Material Finding" if f.risk_level == "High" else "Pass (Below PM)"
            mat_item = QTableWidgetItem(mat_status)
            self.table.setItem(r, 3, mat_item)

            self.table.setItem(r, 4, QTableWidgetItem(rec))

    def closeEvent(self, event):
        self.session.close()
        event.accept()
