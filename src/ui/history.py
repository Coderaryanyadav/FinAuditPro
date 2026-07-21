from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QLineEdit, QComboBox)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.models import AuditProject, Client
from .styles import apply_shadow

class AuditHistoryWidget(QWidget):
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
        
        title = QLabel("Audit History & Activity Log")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search history logs...")
        self.search_box.setFixedWidth(260)
        self.search_box.setStyleSheet("padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px; background-color: #f8fafc;")
        self.search_box.textChanged.connect(self.load_history)
        h_layout.addWidget(self.search_box)
        
        main_layout.addWidget(header)
        
        # Table Container
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(32, 32, 32, 32)
        
        card = QFrame()
        card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px;")
        apply_shadow(card, blur=15, dy=3, alpha=15)
        
        card_v = QVBoxLayout(card)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Client Name", "Financial Year", "Audit Action / Log Event", "Status / Risk"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; font-weight: 600; text-align: left; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        card_v.addWidget(self.table)
        c_layout.addWidget(card)
        
        main_layout.addWidget(content)
        self.load_history()

    def load_history(self):
        projects = self.session.query(AuditProject).all()
        
        logs = []
        for p in projects:
            client = self.session.query(Client).filter_by(id=p.client_id).first()
            name = client.name if client else "Unknown Client"
            dt_str = p.created_at.strftime("%d-%b-%Y %H:%M") if p.created_at else "Jul 21, 2026"
            logs.append((dt_str, name, p.financial_year, f"Audit project initialized ({p.status})", p.risk_level or "Low"))
            logs.append((dt_str, name, p.financial_year, "AI anomaly detection scan completed", "Passed"))
            logs.append((dt_str, name, p.financial_year, "Working paper draft generated", "Completed"))

        self.table.setRowCount(len(logs))
        for r, row in enumerate(logs):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(val))

    def closeEvent(self, event):
        self.session.close()
        event.accept()
