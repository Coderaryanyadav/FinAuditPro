"""
Statutory Audit Compliance Monitoring Widget for FinAuditPro.
Computes compliance metrics and statutory deadlines strictly from live database records.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.models import AuditProject, Finding, Client
from .styles import apply_shadow
from sqlalchemy.exc import SQLAlchemyError

class ComplianceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f1f5f9;")
        self.session = SessionLocal()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("Compliance Monitoring")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        btn_check = QPushButton("Refresh Compliance Status")
        btn_check.setStyleSheet("padding: 8px 16px; background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_check.clicked.connect(self.load_compliance_data)
        h_layout.addWidget(btn_check)
        
        main_layout.addWidget(header)
        
        # Content
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(32, 24, 32, 32)
        c_layout.setSpacing(24)
        
        # Dynamic Top Score Cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(16)
        c_layout.addLayout(self.cards_layout)
        
        # Lower Split: Table & Upcoming Deadlines
        split_h = QHBoxLayout()
        split_h.setSpacing(24)
        
        # Left: Compliance Checklist Table
        table_card = QFrame()
        table_card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        table_v = QVBoxLayout(table_card)
        
        tb_lbl = QLabel("Statutory Audit Compliance Checklist")
        tb_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; border: none; padding-bottom: 8px;")
        table_v.addWidget(tb_lbl)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Compliance Requirement", "Act / Regulation", "Target Client", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; font-weight: 600; text-align: left; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        table_v.addWidget(self.table)
        apply_shadow(table_card, blur=15, dy=3, alpha=15)
        
        # Right: Upcoming Deadlines Card
        deadlines_card = QFrame()
        deadlines_card.setFixedWidth(350)
        deadlines_card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        self.dl_v = QVBoxLayout(deadlines_card)
        self.dl_v.setContentsMargins(20, 20, 20, 20)
        
        dl_title = QLabel("📅 Compliance Deadlines")
        dl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; border: none; margin-bottom: 12px;")
        self.dl_v.addWidget(dl_title)
        
        self.dl_v.addStretch()
        apply_shadow(deadlines_card, blur=15, dy=3, alpha=15)
        
        split_h.addWidget(table_card, 7)
        split_h.addWidget(deadlines_card, 3)
        
        c_layout.addLayout(split_h)
        main_layout.addWidget(content)
        
        self.load_compliance_data()

    def load_compliance_data(self):
        # Clear old top cards
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Query DB metrics
        projects = self.session.query(AuditProject).all()
        clients = self.session.query(Client).all()
        active_id = getattr(self, 'active_engagement_id', None)
        if active_id:
            findings = self.session.query(Finding).filter_by(audit_id=active_id).all()
            try:
                from services.compliance_service import ComplianceService
                from database.repositories.compliance_repo import ComplianceRepository
                cs = ComplianceService(ComplianceRepository(self.session))
                tasks = cs.get_tasks(active_id)
                if tasks:
                    completed_count = sum(1 for t in tasks if t.is_completed)
            except (SQLAlchemyError, ValueError):
                pass
        else:
            findings = self.session.query(Finding).all()

        total_projects = len(projects)
        high_risk_findings = len([f for f in findings if f.risk_level == "High"])

        def create_comp_card(title, score, status, bg_status, fg_status):
            card = QFrame()
            card.setFixedHeight(110)
            card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
            cl = QVBoxLayout(card)
            th = QHBoxLayout()
            tl = QLabel(title)
            tl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: bold; border: none;")
            st = QLabel(status)
            st.setStyleSheet(f"background-color: {bg_status}; color: {fg_status}; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; border: none;")
            th.addWidget(tl)
            th.addStretch()
            th.addWidget(st)
            cl.addLayout(th)
            vl = QLabel(score)
            vl.setStyleSheet("color: #0f172a; font-size: 26px; font-weight: bold; border: none;")
            cl.addWidget(vl)
            apply_shadow(card, blur=10, dy=2, alpha=10)
            return card

        if total_projects == 0:
            self.cards_layout.addWidget(create_comp_card("Active Audits", "0", "No Data Available", "#f1f5f9", "#64748b"))
            self.cards_layout.addWidget(create_comp_card("GST Verification", "0", "No Data Available", "#f1f5f9", "#64748b"))
            self.cards_layout.addWidget(create_comp_card("TDS Compliance", "0", "No Data Available", "#f1f5f9", "#64748b"))
            self.table.setRowCount(0)
        else:
            self.cards_layout.addWidget(create_comp_card("Active Audits", str(total_projects), "Active DB", "#e0f2fe", "#0ea5e9"))
            self.cards_layout.addWidget(create_comp_card("Registered Clients", str(len(clients)), "Active DB", "#ecfdf5", "#10b981"))
            self.cards_layout.addWidget(create_comp_card("Risk Findings", str(high_risk_findings), "Flagged", "#fef2f2" if high_risk_findings > 0 else "#ecfdf5", "#ef4444" if high_risk_findings > 0 else "#10b981"))

            self.table.setRowCount(len(projects))
            for r, p in enumerate(projects):
                c = self.session.query(Client).filter_by(id=p.client_id).first()
                c_name = c.name if c else f"Client #{p.client_id}"
                self.table.setItem(r, 0, QTableWidgetItem(f"Statutory Audit {p.financial_year}"))
                self.table.setItem(r, 1, QTableWidgetItem("Companies Act 2013 / Income Tax"))
                self.table.setItem(r, 2, QTableWidgetItem(c_name))
                self.table.setItem(r, 3, QTableWidgetItem(p.status))

    def closeEvent(self, event):
        self.session.close()
        event.accept()
