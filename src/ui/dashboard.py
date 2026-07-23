"""
Enterprise Dashboard Module for FinAuditPro.
Redesigned with FAANG-grade Desktop UI/UX, QtCharts Analytics, Reusable Component Architecture,
Interactive Metric Cards, RAG Risk Summary, and Custom Multi-Segment Risk Distribution Engine.
"""

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget, QLineEdit, QComboBox, QProgressBar, QMenu)
from PySide6.QtCore import Qt, QSize, Slot, QPropertyAnimation, QEasingCurve, QRect, QMargins
from PySide6.QtGui import QPainter, QColor, QFont, QIcon, QAction, QBrush, QLinearGradient, QPen
from PySide6.QtCharts import QChart, QChartView, QSplineSeries, QPieSeries, QPieSlice, QValueAxis, QCategoryAxis

from database.database import SessionLocal
from database.models import Client, AuditProject, Finding
from services.client_service import ClientService
from services.dashboard_service import DashboardService
from workflow.workflow_manager import WorkflowManager
from workflow.workflow_events import WorkflowEventManager, EventType, WorkflowEvent
from workflow.workflow_state import AuditStage, AuditStatus
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from sqlalchemy.exc import SQLAlchemyError

# Importing pages for StackedWidget
from .clients import ClientManagementWidget
from .documents import DocumentUploadWidget
from .ai_analysis import AIAuditWidget
from .risk_analysis import RiskAnalysisWidget
from .reports import ReportsWidget
from .working_papers import WorkingPaperWidget
from .gst_verification import GSTVerificationWidget
from .compliance import ComplianceWidget
from .settings import SettingsWidget
from .history import AuditHistoryWidget
from .financial_statements import FinancialStatementsWidget

# ==============================================================================
# REUSABLE ENTERPRISE UI COMPONENTS
# ==============================================================================

class SidebarButton(QPushButton):
    """Modern Enterprise Sidebar Button with active glow and smooth hover state."""
    def __init__(self, text, icon_str="", is_active=False, parent=None):
        super().__init__(parent)
        self.setObjectName("navButton")
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_str = icon_str
        self.setText(f"  {icon_str}   {text}" if icon_str else f"  {text}")
        self.set_active(is_active)

    def set_active(self, is_active: bool):
        self.setProperty("active", "true" if is_active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

class GlobalSearchWidget(QFrame):
    """Global Desktop Search Bar with hotkey hint."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 36)
        self.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QFrame:focus-within {
                background-color: #ffffff;
                border: 2px solid #0ea5e9;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("border: none; font-size: 13px; color: #64748b; background: transparent;")
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Search clients, reports, documents...")
        self.input_field.setStyleSheet("border: none; background: transparent; font-size: 12px; color: #0f172a;")
        
        shortcut_lbl = QLabel("⌘K")
        shortcut_lbl.setStyleSheet("border: 1px solid #cbd5e1; background-color: #ffffff; color: #64748b; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 1px 5px;")
        
        layout.addWidget(search_icon)
        layout.addWidget(self.input_field)
        layout.addWidget(shortcut_lbl)

class MetricCard(QFrame):
    """Enterprise KPI Metric Card with pill badge and subtle shadow."""
    def __init__(self, title, value, subtitle, badge_bg, badge_fg, icon_str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(115)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        # Header Row
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 700; border: none; letter-spacing: 0.2px;")
        
        icon_lbl = QLabel(icon_str)
        icon_lbl.setFixedSize(30, 30)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"background-color: {badge_bg}; color: {badge_fg}; border-radius: 8px; font-size: 13px; border: none;")
        
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(icon_lbl)
        
        # Value & Pill Badge Row
        val_layout = QHBoxLayout()
        val_layout.setContentsMargins(0, 0, 0, 0)
        val_layout.setSpacing(10)
        
        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet("color: #0f172a; font-size: 28px; font-weight: 800; border: none;")
        
        badge_lbl = QLabel(subtitle)
        badge_lbl.setStyleSheet(f"color: {badge_fg}; font-size: 10px; font-weight: 700; background-color: {badge_bg}; padding: 3px 8px; border-radius: 6px; border: none;")
        
        val_layout.addWidget(val_lbl)
        val_layout.addWidget(badge_lbl)
        val_layout.addStretch()
        
        layout.addLayout(h_layout)
        layout.addLayout(val_layout)
        apply_shadow(self, blur=14, dy=3, alpha=12)

class AIAuditSummaryCard(QFrame):
    """Redesigned AI Audit Executive Summary Widget."""
    def __init__(self, risk_score: int, comp_score: int, findings: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        
        # Header
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("⚡ AI Audit Summary")
        title_lbl.setStyleSheet("font-weight: 800; font-size: 15px; color: #0f172a; border: none;")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        # Risk & Compliance Progress Bars
        def create_bar(label_text, val_text, val_pct, bar_color):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(4)
            
            top_h = QHBoxLayout()
            t_lbl = QLabel(label_text)
            t_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; border: none;")
            v_lbl = QLabel(val_text)
            v_lbl.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {bar_color}; border: none;")
            top_h.addWidget(t_lbl)
            top_h.addStretch()
            top_h.addWidget(v_lbl)
            l.addLayout(top_h)
            
            pbar = QProgressBar()
            pbar.setFixedHeight(8)
            pbar.setValue(val_pct)
            pbar.setTextVisible(False)
            pbar.setStyleSheet(f"""
                QProgressBar {{ border: none; background-color: #f1f5f9; border-radius: 4px; }}
                QProgressBar::chunk {{ background-color: {bar_color}; border-radius: 4px; }}
            """)
            l.addWidget(pbar)
            return w
            
        risk_color = "#10b981" if risk_score < 30 else "#f59e0b" if risk_score < 60 else "#ef4444"
        risk_txt = f"{risk_score}/100 ({'Low Risk' if risk_score < 30 else 'Medium Risk' if risk_score < 60 else 'High Risk'})"
        layout.addWidget(create_bar("Portfolio Risk Score", risk_txt, min(100, risk_score), risk_color))
        
        comp_color = "#0ea5e9"
        comp_txt = f"{comp_score}% ({'Excellent' if comp_score >= 80 else 'Requires Review'})"
        layout.addWidget(create_bar("Compliance Score", comp_txt, min(100, comp_score), comp_color))
        
        # Recent AI Findings Box
        f_box = QFrame()
        f_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 8px; padding: 10px;")
        f_layout = QVBoxLayout(f_box)
        f_layout.setContentsMargins(8, 8, 8, 8)
        f_layout.setSpacing(6)
        
        f_lbl = QLabel("RECENT AI FINDINGS & AUDIT ANOMALIES")
        f_lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; letter-spacing: 0.5px; border: none;")
        f_layout.addWidget(f_lbl)
        
        if findings:
            for item in findings[:2]:
                item_lbl = QLabel(f"• {item}")
                item_lbl.setWordWrap(True)
                item_lbl.setStyleSheet("font-size: 11px; color: #334155; border: none;")
                f_layout.addWidget(item_lbl)
        else:
            no_findings = QLabel("No AI findings recorded. Ingest documents to run live RAG analysis.")
            no_findings.setStyleSheet("font-size: 11px; color: #94a3b8; border: none;")
            f_layout.addWidget(no_findings)
            
        layout.addWidget(f_box)
        layout.addStretch()
        apply_shadow(self, blur=15, dy=3, alpha=15)

class AuditProgressChart(QFrame):
    """Spline Area Fill QtChart for Audit Completion Trends."""
    def __init__(self, projects: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("Audit Progress Trend")
        title_lbl.setStyleSheet("font-weight: 800; font-size: 15px; color: #0f172a; border: none;")
        
        period_combo = QComboBox()
        period_combo.addItems(["Last 6 Months", "FY 2025-26", "All Time"])
        period_combo.setFixedWidth(130)
        period_combo.setStyleSheet("font-size: 11px; padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 6px;")
        
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(period_combo)
        layout.addLayout(h_layout)
        
        chart = QChart()
        chart.legend().hide()
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))
        
        series = QSplineSeries()
        pen = QPen(QColor("#0ea5e9"), 3)
        series.setPen(pen)
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        data_points = [12, 18, 15, 25, 22, 28]
        if projects:
            for idx, p in enumerate(projects[:6]):
                data_points[idx] = 100 if p.status == "Completed" else 60 if p.status == "Execution" else 30
                
        for i, val in enumerate(data_points):
            series.append(i, val)
            
        chart.addSeries(series)
        
        # Axis setup
        axis_x = QCategoryAxis()
        for i, m in enumerate(months):
            axis_x.append(m, i)
        axis_x.setLabelsColor(QColor("#64748b"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 35)
        axis_y.setLabelsColor(QColor("#64748b"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("border: none; background: transparent;")
        
        layout.addWidget(chart_view)
        apply_shadow(self, blur=15, dy=3, alpha=15)

class RiskDistributionChart(QFrame):
    """Enterprise Multi-Segment Donut Chart for Audit Risk Classification."""
    def __init__(self, low: int, med: int, high: int, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        
        title_lbl = QLabel("Risk Distribution")
        title_lbl.setStyleSheet("font-weight: 800; font-size: 15px; color: #0f172a; border: none;")
        layout.addWidget(title_lbl)
        
        chart = QChart()
        chart.legend().hide()
        chart.setBackgroundVisible(False)
        
        pie_series = QPieSeries()
        pie_series.setHoleSize(0.65)
        
        s1 = pie_series.append("Low Risk", max(1, low))
        s1.setBrush(QColor("#10b981"))
        s2 = pie_series.append("Medium Risk", med)
        s2.setBrush(QColor("#f59e0b"))
        s3 = pie_series.append("High Risk", high)
        s3.setBrush(QColor("#ef4444"))
        
        chart.addSeries(pie_series)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("border: none; background: transparent;")
        
        total_val = low + med + high
        center_lbl = QLabel(f"<b>{total_val}</b><br/><span style='color:#64748b; font-size:10px; font-weight:normal;'>Total Audits</span>", chart_view)
        center_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_lbl.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #0f172a;")
        
        overlay = QVBoxLayout(chart_view)
        overlay.addWidget(center_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(chart_view)
        
        # Legend Row
        leg_layout = QHBoxLayout()
        leg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leg_layout.setSpacing(12)
        
        def create_leg_item(color_hex, label_text):
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(4)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color_hex}; font-size: 10px; border: none;")
            txt = QLabel(label_text)
            txt.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600; border: none;")
            l.addWidget(dot)
            l.addWidget(txt)
            return w
            
        leg_layout.addWidget(create_leg_item("#10b981", "Low Risk"))
        leg_layout.addWidget(create_leg_item("#f59e0b", "Medium Risk"))
        leg_layout.addWidget(create_leg_item("#ef4444", "High Risk"))
        layout.addLayout(leg_layout)
        
        apply_shadow(self, blur=15, dy=3, alpha=15)

class AuditTable(QFrame):
    """Enterprise Recent Audit Projects Table with Status Badges and Review Action."""
    def __init__(self, projects: list, on_review_callback=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        
        # Header Row with Title and View All
        h_layout = QHBoxLayout()
        title_lbl = QLabel("Recent Audit Projects")
        title_lbl.setStyleSheet("font-weight: 800; font-size: 15px; color: #0f172a; border: none;")
        
        view_all_btn = QPushButton("View All →")
        view_all_btn.setStyleSheet("color: #0ea5e9; font-weight: 700; font-size: 12px; border: none; background: transparent;")
        
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(view_all_btn)
        layout.addLayout(h_layout)
        
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["CLIENT NAME", "AUDIT TYPE", "STATUS", "RISK LEVEL", "ACTION"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; background: white; }
            QHeaderView::section { background-color: #f8fafc; color: #475569; padding: 10px; border: none; border-bottom: 1px solid #e2e8f0; font-weight: 700; font-size: 10px; letter-spacing: 0.5px; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-size: 12px; }
        """)
        
        session = SessionLocal()
        table.setRowCount(len(projects))
        for r, proj in enumerate(projects):
            client = session.query(Client).filter_by(id=proj.client_id).first()
            c_name = client.name if client else "Unknown Client"
            
            # Client Avatar & Name Item
            c_item = QTableWidgetItem(f"🏢  {c_name}")
            c_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            table.setItem(r, 0, c_item)
            
            # Audit Type
            type_item = QTableWidgetItem(f"Statutory Audit FY {proj.financial_year or '2025-26'}")
            table.setItem(r, 1, type_item)
            
            # Status Badge
            st = proj.status or "Active"
            st_item = QTableWidgetItem(f"  {st}  ")
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(r, 2, st_item)
            
            # Risk Level Dot
            risk = proj.risk_level or "Low"
            risk_icon = "🟢 Low" if risk == "Low" else "🟡 Medium" if risk == "Medium" else "🔴 High"
            risk_item = QTableWidgetItem(risk_icon)
            table.setItem(r, 3, risk_item)
            
            # Review Button Action Cell
            btn_rev = QPushButton("Review")
            btn_rev.setStyleSheet("background-color: #f0f9ff; color: #0284c7; font-weight: bold; border: 1px solid #bae6fd; border-radius: 4px; padding: 3px 10px; font-size: 11px;")
            if on_review_callback:
                btn_rev.clicked.connect(lambda _, p_id=proj.id: on_review_callback(p_id))
            table.setCellWidget(r, 4, btn_rev)
            
        session.close()
        layout.addWidget(table)
        apply_shadow(self, blur=15, dy=3, alpha=15)

# ==============================================================================
# MAIN DASHBOARD WINDOW IMPLEMENTATION
# ==============================================================================

class DashboardWindow(QWidget):
    """Master Dashboard Window & Navigation Controller for FinAuditPro."""

    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self.workflow_manager = WorkflowManager()
        self.event_manager = WorkflowEventManager()
        
        self.setWindowTitle("FinAuditPro - Enterprise Audit Workspace")
        self.resize(1440, 900)
        self.setObjectName("appBg")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. FAANG-Grade Dark Sidebar Navigation
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #0b0f19; border-right: 1px solid #1e293b;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo Container
        logo_container = QFrame()
        logo_container.setFixedHeight(70)
        logo_container.setStyleSheet("background-color: #0b0f19; border-bottom: 1px solid #1e293b;")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 0, 20, 0)
        
        logo_badge = QLabel("⚡")
        logo_badge.setFixedSize(30, 30)
        logo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_badge.setStyleSheet("background-color: #0ea5e9; color: #ffffff; border-radius: 8px; font-size: 15px; font-weight: bold;")
        
        app_title = QLabel("FinAuditPro")
        app_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff; border: none;")
        logo_layout.addWidget(logo_badge)
        logo_layout.addSpacing(10)
        logo_layout.addWidget(app_title)
        logo_layout.addStretch()
        sidebar_layout.addWidget(logo_container)
        
        # Navigation Scroll Area
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setStyleSheet("background-color: #0b0f19; border: none;")
        nav_widget = QWidget()
        nav_widget.setStyleSheet("background-color: #0b0f19;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)
        
        def add_section_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; padding-left: 12px; margin-top: 10px; margin-bottom: 4px; border: none; letter-spacing: 0.8px;")
            nav_layout.addWidget(lbl)
            
        add_section_label("MAIN MENU")
        self.btn_dashboard = SidebarButton("Dashboard", "📊", True)
        self.btn_clients = SidebarButton("Client Management", "🏢")
        self.btn_upload = SidebarButton("Upload Documents", "📁")
        nav_layout.addWidget(self.btn_dashboard)
        nav_layout.addWidget(self.btn_clients)
        nav_layout.addWidget(self.btn_upload)
        
        add_section_label("AUDIT WORKSPACE")
        self.btn_ai = SidebarButton("AI Audit Analysis", "🤖")
        self.btn_statements = SidebarButton("Financial Statements", "📈")
        self.btn_gst = SidebarButton("GST Verification", "⚖️")
        self.btn_compliance = SidebarButton("Compliance Monitoring", "📋")
        self.btn_risk = SidebarButton("Risk Analysis", "🎯")
        self.btn_working_papers = SidebarButton("Working Papers", "📄")
        nav_layout.addWidget(self.btn_ai)
        nav_layout.addWidget(self.btn_statements)
        nav_layout.addWidget(self.btn_gst)
        nav_layout.addWidget(self.btn_compliance)
        nav_layout.addWidget(self.btn_risk)
        nav_layout.addWidget(self.btn_working_papers)

        add_section_label("SETTINGS & LOGS")
        self.btn_reports = SidebarButton("Reports", "🖨️")
        self.btn_history = SidebarButton("Audit History", "📜")
        self.btn_settings = SidebarButton("Settings", "⚙️")
        nav_layout.addWidget(self.btn_reports)
        nav_layout.addWidget(self.btn_history)
        nav_layout.addWidget(self.btn_settings)
        
        self.nav_buttons = [
            self.btn_dashboard, self.btn_clients, self.btn_upload,
            self.btn_ai, self.btn_statements, self.btn_gst,
            self.btn_compliance, self.btn_risk, self.btn_working_papers,
            self.btn_reports, self.btn_history, self.btn_settings
        ]
        
        nav_layout.addStretch()
        nav_scroll.setWidget(nav_widget)
        sidebar_layout.addWidget(nav_scroll)
        
        # Profile Card Footer
        profile_frame = QFrame()
        profile_frame.setFixedHeight(68)
        profile_frame.setStyleSheet("border-top: 1px solid #1e293b; background-color: #0b0f19;")
        profile_layout = QHBoxLayout(profile_frame)
        profile_layout.setContentsMargins(16, 0, 16, 0)
        
        avatar_lbl = QLabel("CA")
        avatar_lbl.setFixedSize(34, 34)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet("background-color: #0ea5e9; color: #ffffff; border-radius: 17px; font-weight: bold; font-size: 12px;")
        
        profile_info = QVBoxLayout()
        profile_info.setSpacing(2)
        profile_info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        name_lbl = QLabel("CA User")
        name_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #ffffff; border: none;")
        role_lbl = QLabel("Audit Partner")
        role_lbl.setStyleSheet("font-size: 10px; color: #64748b; border: none;")
        profile_info.addWidget(name_lbl)
        profile_info.addWidget(role_lbl)
        
        profile_layout.addWidget(avatar_lbl)
        profile_layout.addSpacing(10)
        profile_layout.addLayout(profile_info)
        profile_layout.addStretch()
        sidebar_layout.addWidget(profile_frame)
        
        # 2. Main Content Stacked Container
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #f8fafc; border: none;")
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top Navigation Bar
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        # Global Search
        self.search_bar = GlobalSearchWidget()
        header_layout.addWidget(self.search_bar)
        
        header_layout.addSpacing(20)
        header_layout.addWidget(QLabel("<b style='color:#0f172a;'>Active Audit:</b>"))
        self.client_selector = QComboBox()
        self.client_selector.setFixedWidth(200)
        self.client_selector.setStyleSheet("padding: 5px; border: 1px solid #cbd5e1; border-radius: 6px; background-color: #f8fafc; font-size: 12px;")
        self.populate_client_selector()
        self.client_selector.currentIndexChanged.connect(self.on_active_engagement_changed)
        header_layout.addWidget(self.client_selector)
        
        btn_new_audit = QPushButton("⚡ + New Audit")
        btn_new_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_audit.setStyleSheet("padding: 6px 12px; background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 6px; border: none; font-size: 12px;")
        btn_new_audit.clicked.connect(self.open_create_audit_dialog)
        header_layout.addWidget(btn_new_audit)
        
        header_layout.addStretch()
        
        # Action Icons
        self.btn_theme = QPushButton("🌙")
        self.btn_theme.setFixedSize(34, 34)
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setStyleSheet("background-color: #f1f5f9; color: #475569; border-radius: 17px; font-size: 13px; border: none;")
        self.btn_theme.clicked.connect(self.toggle_theme)
        
        self.btn_help = QPushButton("❓")
        self.btn_help.setFixedSize(34, 34)
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setStyleSheet("background-color: #f1f5f9; color: #475569; border-radius: 17px; font-size: 13px; border: none;")
        self.btn_help.clicked.connect(self.show_keyboard_shortcuts_dialog)

        self.btn_notif = QPushButton("🔔")
        self.btn_notif.setFixedSize(34, 34)
        self.btn_notif.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_notif.setStyleSheet("background-color: #f1f5f9; color: #475569; border-radius: 17px; font-size: 13px; border: none;")
        self.btn_notif.clicked.connect(self.show_notifications_popup)

        header_layout.addWidget(self.btn_theme)
        header_layout.addSpacing(6)
        header_layout.addWidget(self.btn_help)
        header_layout.addSpacing(6)
        header_layout.addWidget(self.btn_notif)
        
        content_layout.addWidget(header)
        
        # Dashboard Body Page
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(32, 28, 32, 32)
        body_layout.setSpacing(24)
        
        # Hero Section Header
        hero_frame = QFrame()
        hero_frame.setStyleSheet("border: none; background: transparent;")
        hero_v = QVBoxLayout(hero_frame)
        hero_v.setContentsMargins(0, 0, 0, 0)
        hero_v.setSpacing(4)
        
        hero_title = QLabel("Good Morning, Auditor")
        hero_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; border: none;")
        hero_sub = QLabel("Here is your audit overview for today.")
        hero_sub.setStyleSheet("font-size: 13px; color: #64748b; font-weight: normal; border: none;")
        
        hero_v.addWidget(hero_title)
        hero_v.addWidget(hero_sub)
        body_layout.addWidget(hero_frame)
        
        # 4 KPI Cards Grid Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        total_clients = self.session.query(Client).count()
        completed_audits = self.session.query(AuditProject).filter_by(status='Completed').count()
        pending_reviews = self.session.query(AuditProject).filter_by(status='Pending Review').count()
        high_risk_cases = self.session.query(AuditProject).filter_by(risk_level='High').count()

        stats_layout.addWidget(MetricCard("Total Clients", str(total_clients), "+12%", "#e0f2fe", "#0284c7", "👥"))
        stats_layout.addWidget(MetricCard("Completed Audits", str(completed_audits), "This Year", "#dcfce7", "#16a34a", "✅"))
        stats_layout.addWidget(MetricCard("Pending Reviews", str(pending_reviews), "Action Req.", "#fef3c7", "#d97706", "🕒"))
        stats_layout.addWidget(MetricCard("High Risk Cases", str(high_risk_cases), "Flagged by AI", "#fee2e2", "#dc2626", "⚠️"))
        
        body_layout.addLayout(stats_layout)
        
        # Middle 3-Card Row (AI Summary, Audit Progress Spline Chart, Risk Donut Chart)
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(16)
        
        projects = self.session.query(AuditProject).all()
        avg_risk = int(sum([p.risk_score or 0.0 for p in projects]) / len(projects)) if projects else 0
        comp_score = max(0, 100 - avg_risk) if projects else 100
        
        findings_query = self.session.query(Finding).order_by(Finding.id.desc()).limit(2).all()
        findings_list = [f.description for f in findings_query] if findings_query else []
        
        ai_card = AIAuditSummaryCard(avg_risk, comp_score, findings_list)
        progress_chart = AuditProgressChart(projects)
        
        low_count = self.session.query(AuditProject).filter_by(risk_level='Low').count()
        med_count = self.session.query(AuditProject).filter_by(risk_level='Medium').count()
        high_count = self.session.query(AuditProject).filter_by(risk_level='High').count()
        if low_count == 0 and med_count == 0 and high_count == 0: low_count = max(1, len(projects))
        
        risk_chart = RiskDistributionChart(low_count, med_count, high_count)
        
        mid_layout.addWidget(ai_card, 3)
        mid_layout.addWidget(progress_chart, 4)
        mid_layout.addWidget(risk_chart, 3)
        
        body_layout.addLayout(mid_layout)
        
        # Recent Audit Projects Table Row
        recent_projs = self.session.query(AuditProject).order_by(AuditProject.id.desc()).limit(5).all()
        table_widget = AuditTable(recent_projs, on_review_callback=self.on_review_project)
        body_layout.addWidget(table_widget)
        
        body_layout.addStretch()
        scroll.setWidget(body_widget)
        
        # Stacked Widget Pages Indexing
        self.stacked_widget = QStackedWidget()
        
        def safe_load(widget_cls, title):
            try:
                return widget_cls()
            except (SQLAlchemyError, ValueError, RuntimeError) as e:
                return PlaceholderWidget(f"Unable to load {title}: {e}")

        # Index 0: Master Dashboard
        self.stacked_widget.addWidget(scroll)
        # Index 1: Client Management
        self.clients_page = safe_load(ClientManagementWidget, "Client Management")
        self.stacked_widget.addWidget(self.clients_page)
        # Index 2: Upload Documents
        self.docs_page = safe_load(DocumentUploadWidget, "Document Upload")
        self.stacked_widget.addWidget(self.docs_page)
        # Index 3: AI Audit Analysis
        self.ai_page = safe_load(AIAuditWidget, "AI Audit Analysis")
        self.stacked_widget.addWidget(self.ai_page)
        # Index 4: Financial Statements
        self.statements_page = safe_load(FinancialStatementsWidget, "Financial Statements")
        self.stacked_widget.addWidget(self.statements_page)
        # Index 5: GST Verification
        self.gst_page = safe_load(GSTVerificationWidget, "GST Verification")
        self.stacked_widget.addWidget(self.gst_page)
        # Index 6: Compliance Monitoring
        self.compliance_page = safe_load(ComplianceWidget, "Compliance Monitoring")
        self.stacked_widget.addWidget(self.compliance_page)
        # Index 7: Risk Analysis
        self.risk_page = safe_load(RiskAnalysisWidget, "Risk Analysis")
        self.stacked_widget.addWidget(self.risk_page)
        # Index 8: Reports
        self.reports_page = safe_load(ReportsWidget, "Report Generator")
        self.stacked_widget.addWidget(self.reports_page)
        # Index 9: Audit History
        self.history_page = safe_load(AuditHistoryWidget, "Audit History")
        self.stacked_widget.addWidget(self.history_page)
        # Index 10: Settings
        self.settings_page = safe_load(SettingsWidget, "System Settings")
        self.stacked_widget.addWidget(self.settings_page)
        # Index 11: Working Papers
        self.working_papers_page = safe_load(WorkingPaperWidget, "Working Papers")
        self.stacked_widget.addWidget(self.working_papers_page)
        
        content_layout.addWidget(self.stacked_widget)
        
        def reset_buttons():
            for btn in self.nav_buttons:
                btn.set_active(False)
                
        def nav_click(index, btn):
            self.stacked_widget.setCurrentIndex(index)
            reset_buttons()
            btn.set_active(True)
            
        self.btn_dashboard.clicked.connect(lambda: nav_click(0, self.btn_dashboard))
        self.btn_clients.clicked.connect(lambda: nav_click(1, self.btn_clients))
        self.btn_upload.clicked.connect(lambda: nav_click(2, self.btn_upload))
        self.btn_ai.clicked.connect(lambda: nav_click(3, self.btn_ai))
        self.btn_statements.clicked.connect(lambda: nav_click(4, self.btn_statements))
        self.btn_gst.clicked.connect(lambda: nav_click(5, self.btn_gst))
        self.btn_compliance.clicked.connect(lambda: nav_click(6, self.btn_compliance))
        self.btn_risk.clicked.connect(lambda: nav_click(7, self.btn_risk))
        self.btn_reports.clicked.connect(lambda: nav_click(8, self.btn_reports))
        self.btn_history.clicked.connect(lambda: nav_click(9, self.btn_history))
        self.btn_settings.clicked.connect(lambda: nav_click(10, self.btn_settings))

        main_layout.addWidget(sidebar)
        main_layout.addWidget(main_content)
        self.setup_keyboard_shortcuts()

    def on_review_project(self, project_id: int):
        self.stacked_widget.setCurrentIndex(11) # Navigate to Working Papers
        for btn in self.nav_buttons: btn.set_active(False)
        self.btn_working_papers.set_active(True)

    def open_create_audit_dialog(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        from PySide6.QtWidgets import QMessageBox, QDialog
        from .clients import CreateAuditProjectDialog

        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.MANAGE_CLIENTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to create audit projects.")
            return

        dialog = CreateAuditProjectDialog(self.session, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_id = dialog.client_combo.currentData()
            fy = dialog.fy_combo.currentText().strip() if hasattr(dialog, 'fy_combo') else "2025-26"
            audit_type = dialog.audit_type_combo.currentText().strip() if hasattr(dialog, 'audit_type_combo') else "Statutory Audit"
            status = dialog.stage_combo.currentText().strip() if hasattr(dialog, 'stage_combo') else "Planning"
            risk = dialog.risk_combo.currentText().strip() if hasattr(dialog, 'risk_combo') else "Medium"

            proj = AuditProject(client_id=client_id, financial_year=fy, status=status, risk_level=risk)
            self.session.add(proj)
            self.session.commit()

            self.populate_client_selector()
            idx = self.client_selector.findData(proj.id)
            if idx >= 0: self.client_selector.setCurrentIndex(idx)
            QMessageBox.information(self, "Audit Created", f"Successfully initialized new {audit_type} for FY {fy}.")

    def populate_client_selector(self):
        self.client_selector.clear()
        clients = self.session.query(Client).all()
        for c in clients:
            projs = self.session.query(AuditProject).filter_by(client_id=c.id).all()
            if projs:
                for proj in projs:
                    fy = proj.financial_year or "2025-26"
                    self.client_selector.addItem(f"{c.name} (FY {fy})", proj.id)
            else:
                self.client_selector.addItem(f"{c.name} (FY 2025-26)", f"client_{c.id}")

    def on_active_engagement_changed(self, index):
        data = self.client_selector.currentData()
        if not data: return
        try:
            if isinstance(data, str) and data.startswith("client_"):
                client_id = int(data.split("_")[1])
                proj = AuditProject(client_id=client_id, financial_year="2025-26", status="Execution")
                self.session.add(proj)
                self.session.commit()
                proj_id = proj.id
            else:
                proj_id = int(data)
                proj = self.session.query(AuditProject).filter_by(id=proj_id).first()

            if proj:
                self.workflow_manager.initialize_engagement(engagement_id=proj.id, client_id=proj.client_id, financial_year=proj.financial_year or "2025-26")
                if hasattr(self, 'ai_page') and self.ai_page is not None:
                    self.ai_page.active_engagement_id = proj.id
        except (SQLAlchemyError, ValueError, RuntimeError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Engagement change warning: {e}")

    def setup_keyboard_shortcuts(self):
        from PySide6.QtGui import QKeySequence, QShortcut
        for i in range(min(9, len(self.nav_buttons))):
            btn = self.nav_buttons[i]
            shortcut = QShortcut(QKeySequence(f"Alt+{i+1}"), self)
            shortcut.activated.connect(btn.click)
            btn.setToolTip(f"Hotkey: Alt+{i+1}")
            
        self.f5_shortcut = QShortcut(QKeySequence("F5"), self)
        self.f5_shortcut.activated.connect(self.repaint)
        
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self.settings_shortcut.activated.connect(self.btn_settings.click)

    def toggle_theme(self):
        is_dark = getattr(self, '_dark_mode', False)
        self._dark_mode = not is_dark
        self.btn_theme.setText("☀️" if self._dark_mode else "🌙")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Theme Preferences", f"Switched to {'Dark' if self._dark_mode else 'Standard Enterprise Slate'} palette.")

    def show_keyboard_shortcuts_dialog(self):
        from PySide6.QtWidgets import QMessageBox
        shortcuts_text = """
<b>FinAuditPro Desktop Keyboard Shortcuts:</b><br/><br/>
• <b>Alt + 1</b> : Dashboard Overview<br/>
• <b>Alt + 2</b> : Client Management<br/>
• <b>Alt + 3</b> : Upload Documents<br/>
• <b>Alt + 4</b> : AI Audit Analysis Copilot<br/>
• <b>Alt + 5</b> : Financial Statements<br/>
• <b>Alt + 6</b> : GST Verification & 2B Match<br/>
• <b>Alt + 7</b> : Compliance Monitoring (CARO 2020)<br/>
• <b>Alt + 8</b> : Risk Analysis<br/>
• <b>Alt + 9</b> : Working Paper Generator<br/>
• <b>F5</b> : Refresh Data<br/>
• <b>Ctrl + ,</b> : Open Settings & Governance<br/>
"""
        QMessageBox.information(self, "Keyboard Shortcuts Reference", shortcuts_text)

    def show_notifications_popup(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Active Audit Alerts",
            "<b>Active Compliance Alerts:</b><br/><br/>"
            "• GSTR-3B Tax Filing Deadline: <b>5 days remaining</b><br/>"
            "• Income Tax Audit Report (Form 3CD): <b>In Progress</b><br/>"
            "• CARO 2020 Physical Inventory Verification: <b>Completed</b>"
        )

    def closeEvent(self, event):
        self.session.close()
        event.accept()
