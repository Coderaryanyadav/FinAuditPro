from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QTableWidget, 
                               QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.models import Finding, AuditProject
from sqlalchemy.exc import SQLAlchemyError

def create_risk_card(title, count, bg_color, text_color):
    card = QFrame()
    card.setFixedHeight(120)
    card.setStyleSheet(f"background-color: {bg_color}; border-radius: 12px; border: 1px solid {text_color}33;")
    clayout = QVBoxLayout(card)
    
    t_lbl = QLabel(title)
    t_lbl.setStyleSheet(f"color: {text_color}; font-size: 14px; font-weight: bold; border: none;")
    
    v_lbl = QLabel(str(count))
    v_lbl.setStyleSheet(f"color: {text_color}; font-size: 36px; font-weight: bold; border: none;")
    
    clayout.addWidget(t_lbl)
    clayout.addWidget(v_lbl)
    clayout.addStretch()
    
    return card

class RiskAnalysisWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.session = SessionLocal()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("Risk Analysis")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        h_layout.addWidget(title)
        
        action_btn = QPushButton("Generate Risk Report")
        action_btn.setStyleSheet("background-color: #0ea5e9; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        h_layout.addStretch()
        h_layout.addWidget(action_btn)
        
        main_layout.addWidget(header)
        
        # Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(32, 32, 32, 32)
        b_layout.setSpacing(24)
        
        # Fetch counts from database
        active_id = getattr(self, 'active_engagement_id', None)
        if active_id:
            high_count = self.session.query(Finding).filter_by(audit_id=active_id, risk_level='High').count()
            med_count = self.session.query(Finding).filter_by(audit_id=active_id, risk_level='Medium').count()
            low_count = self.session.query(Finding).filter_by(audit_id=active_id, risk_level='Low').count()
        else:
            high_count = self.session.query(Finding).filter_by(risk_level='High').count()
            med_count = self.session.query(Finding).filter_by(risk_level='Medium').count()
            low_count = self.session.query(Finding).filter_by(risk_level='Low').count()
        
        # Risk Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)
        cards_layout.addWidget(create_risk_card("High Risk", high_count, "#fef2f2", "#ef4444"))
        cards_layout.addWidget(create_risk_card("Medium Risk", med_count, "#fffbeb", "#f59e0b"))
        cards_layout.addWidget(create_risk_card("Low Risk", low_count, "#ecfdf5", "#10b981"))
        b_layout.addLayout(cards_layout)
        
        # Findings Table
        table_container = QFrame()
        table_container.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        t_layout = QVBoxLayout(table_container)
        
        t_title = QLabel("Detected Risk Findings")
        t_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; padding: 12px; border-bottom: 1px solid #e2e8f0;")
        t_layout.addWidget(t_title)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Issue", "Risk Level", "Amount Reference", "Evidence Source", "Recommendation"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #334155; padding: 10px; border: none; border-bottom: 2px solid #e2e8f0; font-weight: 700; text-transform: uppercase; font-size: 11px; text-align: left; }
            QTableWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        t_layout.addWidget(self.table)
        b_layout.addWidget(table_container)
        
        b_layout.addStretch()
        scroll.setWidget(body)
        main_layout.addWidget(scroll)
        
        self.load_findings()

    def load_findings(self):
        active_id = getattr(self, 'active_engagement_id', None)
        if active_id:
            try:
                from services.risk_service import RiskService
                from database.repositories.risk_repo import RiskRepository
                rs = RiskService(RiskRepository(self.session))
            except (SQLAlchemyError, ValueError):
                pass
            findings = self.session.query(Finding).filter_by(audit_id=active_id).all()
        else:
            findings = self.session.query(Finding).all()
        self.table.setRowCount(0)
        for r, f in enumerate(findings):
            self.table.insertRow(r)
            
            # Extract fields from description string formatted as "Issue | Amount | Evidence | Rec"
            parts = [p.strip() for p in f.description.split("|")]
            issue = parts[0] if len(parts) > 0 else f.description
            amount = parts[1] if len(parts) > 1 else "N/A"
            evidence = parts[2] if len(parts) > 2 else "N/A"
            rec = parts[3] if len(parts) > 3 else "N/A"
            
            self.table.setItem(r, 0, QTableWidgetItem(issue))
            self.table.setItem(r, 1, QTableWidgetItem(f.risk_level))
            self.table.setItem(r, 2, QTableWidgetItem(amount))
            self.table.setItem(r, 3, QTableWidgetItem(evidence))
            self.table.setItem(r, 4, QTableWidgetItem(rec))

    def closeEvent(self, event):
        self.session.close()
        event.accept()
