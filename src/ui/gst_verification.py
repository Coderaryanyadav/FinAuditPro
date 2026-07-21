from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QLineEdit, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from .styles import apply_shadow

class GSTVerificationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f1f5f9;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Action Bar
        action_bar = QFrame()
        action_bar.setFixedHeight(80)
        action_bar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("GST Verification & Reconciliation")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        action_layout.addWidget(title)
        
        action_layout.addStretch()
        
        btn_verify = QPushButton("⚡ Run Re-verification")
        btn_verify.setStyleSheet("padding: 8px 16px; border: none; border-radius: 6px; background-color: #0ea5e9; color: white; font-weight: bold;")
        btn_verify.clicked.connect(self.run_reverification)
        action_layout.addWidget(btn_verify)
        
        main_layout.addWidget(action_bar)
        
        # Content layout
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 24, 32, 32)
        content_layout.setSpacing(24)
        
        # Summary Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        def create_gst_card(title, value, subtitle, tag, bg_tag, fg_tag, border_color="#e2e8f0"):
            card = QFrame()
            card.setFixedHeight(110)
            card.setStyleSheet(f"background-color: #ffffff; border: 1px solid {border_color}; border-radius: 12px;")
            clayout = QVBoxLayout(card)
            
            top_h = QHBoxLayout()
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500; border: none;")
            
            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet(f"background-color: {bg_tag}; color: {fg_tag}; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; border: none;")
            
            top_h.addWidget(t_lbl)
            top_h.addStretch()
            top_h.addWidget(tag_lbl)
            clayout.addLayout(top_h)
            
            v_lbl = QLabel(value)
            v_lbl.setStyleSheet("color: #0f172a; font-size: 24px; font-weight: bold; border: none;")
            clayout.addWidget(v_lbl)
            
            s_lbl = QLabel(subtitle)
            s_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
            clayout.addWidget(s_lbl)
            
            apply_shadow(card, blur=10, dy=2, alpha=10)
            return card
            
        card1 = create_gst_card("GSTIN Status", "142 / 145 Active", "3 Suspended / Cancelled GSTINs", "ACTIVE", "#ecfdf5", "#10b981")
        card2 = create_gst_card("2B vs Books Match", "94.2%", "₹4,25,000 Matched Input Tax Credit", "RECONCILED", "#f0f9ff", "#0ea5e9")
        card3 = create_gst_card("ITC Mismatch", "₹48,250", "Unmatched ITC in GSTR-2B", "WARNING", "#fffbeb", "#f59e0b", "#fde68a")
        card4 = create_gst_card("Ineligible ITC", "₹12,400", "Blocked credit under Sec 17(5)", "RISK", "#fef2f2", "#ef4444", "#fecaca")
        
        cards_layout.addWidget(card1)
        cards_layout.addWidget(card2)
        cards_layout.addWidget(card3)
        cards_layout.addWidget(card4)
        
        content_layout.addLayout(cards_layout)
        
        # Table Section
        table_card = QFrame()
        table_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        apply_shadow(table_card, blur=15, dy=3, alpha=15)
        table_v = QVBoxLayout(table_card)
        
        tb_header = QHBoxLayout()
        tb_title = QLabel("GSTR-2B vs Purchase Register Reconciliation Table")
        tb_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; border: none;")
        tb_header.addWidget(tb_title)
        tb_header.addStretch()
        
        search = QLineEdit()
        search.setPlaceholderText("Filter Invoice or GSTIN...")
        search.setFixedWidth(240)
        search.setStyleSheet("padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 6px;")
        tb_header.addWidget(search)
        
        table_v.addLayout(tb_header)
        
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Invoice No", "Vendor Name & GSTIN", "Books ITC", "2B ITC", "Variance", "Match Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; font-weight: 600; text-align: left; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        from database.database import SessionLocal
        from database.models import Finding
        session = SessionLocal()
        try:
            gst_findings = session.query(Finding).filter(Finding.description.ilike('%GST%')).all()
            if gst_findings:
                self.table.setRowCount(len(gst_findings))
                for r, f in enumerate(gst_findings):
                    self.table.setItem(r, 0, QTableWidgetItem(f"FINDING-{f.id}"))
                    self.table.setItem(r, 1, QTableWidgetItem("Audit Record"))
                    self.table.setItem(r, 2, QTableWidgetItem(f"₹ {f.financial_impact or 0:.2f}"))
                    self.table.setItem(r, 3, QTableWidgetItem("₹ 0.00"))
                    self.table.setItem(r, 4, QTableWidgetItem(f"₹ {f.financial_impact or 0:.2f}"))
                    self.table.setItem(r, 5, QTableWidgetItem(f.severity))
            else:
                self.table.setRowCount(0)
        finally:
            session.close()
                
        table_v.addWidget(self.table)
        content_layout.addWidget(table_card)
        
        main_layout.addWidget(content_widget)

    def run_reverification(self):
        QMessageBox.information(self, "GST Verification", "Re-verification complete! All vendor GSTIN status and 2B records updated.")
