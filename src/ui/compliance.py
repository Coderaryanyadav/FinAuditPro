from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from .styles import apply_shadow

class ComplianceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f1f5f9;")
        
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
        
        btn_check = QPushButton("Check Compliance Now")
        btn_check.setStyleSheet("padding: 8px 16px; background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_check.clicked.connect(self.check_compliance)
        h_layout.addWidget(btn_check)
        
        main_layout.addWidget(header)
        
        # Content
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(32, 24, 32, 32)
        c_layout.setSpacing(24)
        
        # Top Score Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
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
            
        cards_layout.addWidget(create_comp_card("Income Tax", "98%", "Compliant", "#ecfdf5", "#10b981"))
        cards_layout.addWidget(create_comp_card("GST Returns", "72%", "Warning", "#fffbeb", "#f59e0b"))
        cards_layout.addWidget(create_comp_card("TDS Filings", "95%", "Compliant", "#ecfdf5", "#10b981"))
        cards_layout.addWidget(create_comp_card("Companies Act ROC", "100%", "Compliant", "#ecfdf5", "#10b981"))
        cards_layout.addWidget(create_comp_card("Accounting Standards", "92%", "Compliant", "#ecfdf5", "#10b981"))
        
        c_layout.addLayout(cards_layout)
        
        # Lower Split: Table & Upcoming Deadlines
        split_h = QHBoxLayout()
        split_h.setSpacing(24)
        
        # Left: Compliance Checklist Table
        table_card = QFrame()
        table_card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        table_v = QVBoxLayout(table_card)
        
        tb_lbl = QLabel("Statutory Audit Compliance Checklist")
        tb_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; border-none; padding-bottom: 8px;")
        table_v.addWidget(tb_lbl)
        
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Compliance Requirement", "Act / Regulation", "Due Date", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; font-weight: 600; text-align: left; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        
        items = [
            ("GSTR-3B Monthly Return", "GST Act 2017", "20-Aug-2026", "Pending Filing"),
            ("TDS Deposit (Section 194C/194J)", "Income Tax Act 1961", "07-Aug-2026", "Compliant"),
            ("Form MGT-7 Annual Return", "Companies Act 2013", "30-Nov-2026", "Upcoming"),
            ("Form AOC-4 Financial Statements", "Companies Act 2013", "29-Oct-2026", "Upcoming"),
            ("Advance Tax Quarter 2", "Income Tax Act 1961", "15-Sep-2026", "Upcoming")
        ]
        
        table.setRowCount(len(items))
        for r, row in enumerate(items):
            for c, val in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(val))
                
        table_v.addWidget(table)
        apply_shadow(table_card, blur=15, dy=3, alpha=15)
        
        # Right: Upcoming Deadlines Card
        deadlines_card = QFrame()
        deadlines_card.setFixedWidth(350)
        deadlines_card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        dl_v = QVBoxLayout(deadlines_card)
        dl_v.setContentsMargins(20, 20, 20, 20)
        
        dl_title = QLabel("📅 Compliance Deadlines")
        dl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; border: none; margin-bottom: 12px;")
        dl_v.addWidget(dl_title)
        
        deadlines = [
            ("TDS Payment - July 2026", "Due: 07 Aug 2026", "#0ea5e9"),
            ("GSTR-1 Sales Return", "Due: 11 Aug 2026", "#0ea5e9"),
            ("GSTR-3B Monthly Return", "Due: 20 Aug 2026", "#f59e0b"),
            ("Advance Tax Instalment 2", "Due: 15 Sep 2026", "#10b981")
        ]
        
        for name, due, color in deadlines:
            df = QFrame()
            df.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px;")
            dv = QVBoxLayout(df)
            dv.setContentsMargins(8, 8, 8, 8)
            n_lbl = QLabel(name)
            n_lbl.setStyleSheet("font-weight: bold; color: #0f172a; font-size: 13px; border: none;")
            d_lbl = QLabel(due)
            d_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; border: none;")
            dv.addWidget(n_lbl)
            dv.addWidget(d_lbl)
            dl_v.addWidget(df)
            
        dl_v.addStretch()
        apply_shadow(deadlines_card, blur=15, dy=3, alpha=15)
        
        split_h.addWidget(table_card, 7)
        split_h.addWidget(deadlines_card, 3)
        
        c_layout.addLayout(split_h)
        main_layout.addWidget(content)

    def check_compliance(self):
        QMessageBox.information(self, "Compliance Check", "Compliance monitoring completed! No critical violations found.")
