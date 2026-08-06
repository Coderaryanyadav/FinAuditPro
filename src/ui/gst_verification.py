from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLineEdit, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from database.database import get_session
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.finding_service import FindingService
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget

class GSTVerificationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #0f172a;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Action Bar — Apple Header
        action_bar = QFrame()
        action_bar.setFixedHeight(68)
        action_bar.setObjectName("gstHeader")
        action_bar.setStyleSheet("background-color: #1e293b; border-bottom: 1px solid #334155;")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("GST 2B vs Purchase Register Reconciliation Engine")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc; letter-spacing: -0.4px; border: none; background: transparent;")
        subtitle = QLabel("Automated Input Tax Credit (ITC) Mismatch & Vendor Non-Compliance Finder")
        subtitle.setStyleSheet("font-size: 12px; color: #94a3b8; border: none; background: transparent;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        action_layout.addLayout(title_v)
        
        action_layout.addStretch()
        
        btn_verify = QPushButton("Refresh Findings")
        btn_verify.setToolTip("Reload GST findings from the database")
        btn_verify.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn_verify.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #0062cc; }
        """)
        btn_verify.clicked.connect(self.load_data)
        action_layout.addWidget(btn_verify)
        
        main_layout.addWidget(action_bar)
        
        # Content layout
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 24, 32, 32)
        content_layout.setSpacing(24)
        
        # Summary Cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)
        content_layout.addLayout(self.cards_layout)
        
        # Table Section
        table_card = QFrame()
        table_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e5e5ea; border-radius: 12px;")
        apply_shadow(table_card, blur=15, dy=3, alpha=6)
        self.table_v = QVBoxLayout(table_card)
        
        tb_header = QHBoxLayout()
        tb_title = QLabel("GST Findings Registry")
        tb_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f; letter-spacing: -0.4px; border: none;")
        tb_header.addWidget(tb_title)
        tb_header.addStretch()
        
        search = QLineEdit()
        search.setPlaceholderText("Filter Findings...")
        search.setFixedWidth(240)
        search.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        search.setStyleSheet("padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 6px;")
        tb_header.addWidget(search)
        
        self.table_v.addLayout(tb_header)
        
        self.table = QTableWidget(0, 4)
        self.table.setToolTip("GST Findings Registry")
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.setHorizontalHeaderLabels(["Finding ID", "Description", "Financial Impact", "Severity"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; font-weight: 600; text-align: left; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table_v.addWidget(self.table)
        
        content_layout.addWidget(table_card)
        main_layout.addWidget(content_widget)
        
        # Initialize placeholders
        self.empty_widget = None
        self.error_widget = None
        self.load_data()

    def create_gst_card(self, title, value, subtitle, tag, bg_tag, fg_tag, border_color="#e5e5ea"):
        card = QFrame()
        card.setFixedHeight(110)
        card.setStyleSheet(f"background-color: #ffffff; border: 1px solid {border_color}; border-radius: 12px;")
        clayout = QVBoxLayout(card)
        
        top_h = QHBoxLayout()
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #1d1d1f; font-size: 13px; font-weight: 600; border: none;")
        
        tag_lbl = QLabel(tag)
        tag_lbl.setStyleSheet(f"background-color: {bg_tag}; color: {fg_tag}; font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 4px; border: none;")
        
        top_h.addWidget(t_lbl)
        top_h.addStretch()
        top_h.addWidget(tag_lbl)
        clayout.addLayout(top_h)
        
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet("color: #1d1d1f; font-size: 24px; font-weight: 600; letter-spacing: -0.5px; border: none;")
        clayout.addWidget(v_lbl)
        
        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet("color: #6e6e73; font-size: 11px; border: none;")
        clayout.addWidget(s_lbl)
        
        apply_shadow(card, blur=10, dy=2, alpha=6)
        return card

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def load_data(self):
        # Clear existing cards and table messages
        self.clear_layout(self.cards_layout)
        if self.empty_widget:
            self.empty_widget.deleteLater()
            self.empty_widget = None
        if self.error_widget:
            self.error_widget.deleteLater()
            self.error_widget = None

        active_id = getattr(self, 'active_engagement_id', None)
        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                finding_service = FindingService(wp_repo)
                if active_id:
                    all_f = finding_service.get_findings_by_audit_id(active_id)
                else:
                    all_f = finding_service.get_all_findings()
                
                gst_findings = [f for f in all_f if 'gst' in str(f.description or '').lower()]
                
                # Compute Real values
                total_mismatch = sum(f.financial_impact or 0 for f in gst_findings if 'mismatch' in str(f.description or '').lower())
                total_ineligible = sum(f.financial_impact or 0 for f in gst_findings if 'ineligible' in str(f.description or '').lower() or '17(5)' in str(f.description or '').lower())
                
                # If the description doesn't specify, just sum all for total impact to be safe
                if total_mismatch == 0 and total_ineligible == 0:
                    total_mismatch = sum(f.financial_impact or 0 for f in gst_findings)
                
                # Add cards
                card1 = self.create_gst_card("GSTIN Status", "N/A", "Data source not configured", "UNAVAILABLE", "#f2f2f7", "#8e8e93")
                card2 = self.create_gst_card("2B vs Books Match", "N/A", "GSTR-2B sync unavailable", "UNAVAILABLE", "#f2f2f7", "#8e8e93")
                card3 = self.create_gst_card("ITC Mismatch", f"₹{total_mismatch:,.2f}", "Total mismatch impact", "WARNING", "#fff8e6", "#ff9500", "#ffe0b2")
                card4 = self.create_gst_card("Ineligible ITC", f"₹{total_ineligible:,.2f}", "Total ineligible impact", "RISK", "#ffebeb", "#ff3b30", "#ffc6c4")
                
                self.cards_layout.addWidget(card1)
                self.cards_layout.addWidget(card2)
                self.cards_layout.addWidget(card3)
                self.cards_layout.addWidget(card4)
                
                if gst_findings:
                    self.table.setRowCount(len(gst_findings))
                    self.table.show()
                    for r, f in enumerate(gst_findings):
                        self.table.setItem(r, 0, QTableWidgetItem(f"FINDING-{f.id}"))
                        desc = f.description if f.description else "Audit Record"
                        self.table.setItem(r, 1, QTableWidgetItem(desc))
                        self.table.setItem(r, 2, QTableWidgetItem(f"₹ {f.financial_impact or 0:,.2f}"))
                        self.table.setItem(r, 3, QTableWidgetItem(f.severity or "Medium"))
                else:
                    self.table.setRowCount(0)
                    self.table.hide()
                    self.empty_widget = EmptyStateWidget("No GST Findings", "No GST-related issues or anomalies flagged.")
                    self.table_v.addWidget(self.empty_widget)
        except Exception as e:
            self.table.setRowCount(0)
            self.table.hide()
            self.error_widget = ErrorStateWidget("GST Data Error", str(e))
            self.table_v.addWidget(self.error_widget)
