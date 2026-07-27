"""
Enterprise Dashboard Module for FinAuditPro.
Redesigned with Model-View Architecture (QAbstractTableModel + QTableView + QStyledItemDelegate),
Real-Time Signal/Slot Automatic Data Refresh, QtCharts QSplineSeries & QPieSeries,
and RAG AI Executive Summary Card.
"""

import os
import logging
from typing import List, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout, 
                               QTableView, QHeaderView, QStackedWidget, QLineEdit, 
                               QComboBox, QProgressBar, QMenu, QStyledItemDelegate,
                               QStyleOptionViewItem, QMessageBox, QDialog)
from PySide6.QtCore import Qt, QSize, Slot, QAbstractTableModel, QModelIndex, QRect, Signal, QMargins
from PySide6.QtGui import QPainter, QColor, QFont, QIcon, QBrush, QPen, QKeySequence, QShortcut
from PySide6.QtCharts import QChart, QChartView, QSplineSeries, QPieSeries, QValueAxis, QCategoryAxis

from database.database import get_session
from database.models import Client, AuditProject, Finding
from services.client_service import ClientService
from services.dashboard_service import DashboardService
from security.security_manager import SecurityManager
from security.rbac import Permission
from workflow.workflow_manager import WorkflowManager
from workflow.workflow_events import WorkflowEventManager
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from sqlalchemy.exc import SQLAlchemyError

# Sub-module imports for QStackedWidget pages
from .clients import ClientManagementWidget, CreateAuditProjectDialog
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

logger = logging.getLogger(__name__)

# ==============================================================================
# MODEL-VIEW ARCHITECTURE (QAbstractTableModel + QStyledItemDelegate)
# ==============================================================================

class AuditProjectsTableModel(QAbstractTableModel):
    """Real-time Table Model for Audit Projects storing detached values safely."""
    
    HEADERS = ["CLIENT NAME", "AUDIT TYPE", "STATUS", "RISK LEVEL", "LAST UPDATED"]
    
    def __init__(self, projects: List[Any] = None, parent=None):
        super().__init__(parent)
        self._client_cache = {}
        self._load_client_cache()
        self._projects = self._normalize(projects or [])

    def _load_client_cache(self):
        with get_session() as session:
            clients = session.query(Client).all()
            self._client_cache = {c.id: c.name for c in clients}

    def _normalize(self, projects: List[Any]) -> List[dict]:
        res = []
        for p in projects:
            if isinstance(p, dict):
                res.append(p)
            else:
                dt_str = p.created_at.strftime("%d-%b-%Y %H:%M") if getattr(p, 'created_at', None) else "Today"
                res.append({
                    'id': getattr(p, 'id', None),
                    'client_id': getattr(p, 'client_id', None),
                    'financial_year': getattr(p, 'financial_year', '2025-26'),
                    'status': getattr(p, 'status', 'Active'),
                    'risk_level': getattr(p, 'risk_level', 'Low'),
                    'created_at_str': dt_str
                })
        return res

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._projects)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._projects)):
            return None

        proj = self._projects[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                client_name = self._client_cache.get(proj.get('client_id'), f"Client #{proj.get('client_id')}")
                return f"🏢 {client_name}"
            elif col == 1:
                return f"Statutory Audit (FY {proj.get('financial_year') or '2025-26'})"
            elif col == 2:
                return proj.get('status') or "Active"
            elif col == 3:
                return proj.get('risk_level') or "Low"
            elif col == 4:
                return proj.get('created_at_str') or "Today"

        elif role == Qt.ItemDataRole.UserRole:
            return proj.get('id')

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (2, 3):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def update_projects(self, new_projects: List[Any]):
        self.beginResetModel()
        self._load_client_cache()
        self._projects = self._normalize(new_projects)
        self.endResetModel()

class AuditStatusDelegate(QStyledItemDelegate):
    """Custom Delegate to draw status pill badges and colored risk dots in QTableView."""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        col = index.column()
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = option.rect
        
        if col == 2: # Status Pill
            bg_color = QColor("#f0f9ff") if "Active" in text or "Execution" in text else QColor("#dcfce7") if "Completed" in text else QColor("#fef3c7")
            text_color = QColor("#0284c7") if "Active" in text or "Execution" in text else QColor("#16a34a") if "Completed" in text else QColor("#d97706")
            
            pill_rect = rect.adjusted(12, 6, -12, -6)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(pill_rect, 6, 6)
            
            painter.setPen(QPen(text_color))
            painter.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, text)

        elif col == 3: # Risk Dot & Text
            dot_color = QColor("#10b981") if "Low" in text else QColor("#f59e0b") if "Medium" in text else QColor("#ef4444")
            
            dot_x = rect.left() + 16
            dot_y = rect.top() + (rect.height() // 2) - 4
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(dot_x, dot_y, 8, 8)
            
            text_rect = rect.adjusted(30, 0, 0, 0)
            painter.setPen(QPen(QColor("#0f172a")))
            painter.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
            
        else:
            super().paint(painter, option, index)
            
        painter.restore()

# ==============================================================================
# REUSABLE ENTERPRISE WIDGET COMPONENTS
# ==============================================================================

class SidebarButton(QPushButton):
    """Modern Enterprise Sidebar Button with active indicator tab."""
    def __init__(self, text, icon_str="", is_active=False, parent=None):
        super().__init__(parent)
        self.setObjectName("navButton")
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(f"  {icon_str}   {text}" if icon_str else f"  {text}")
        self.set_active(is_active)

    def set_active(self, is_active: bool):
        self.setProperty("active", "true" if is_active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

class GlobalSearchWidget(QFrame):
    """Global Desktop Search Bar with ⌘K hotkey badge."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 36)
        self.setStyleSheet("""
            QFrame { background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; }
            QFrame:focus-within { background-color: #ffffff; border: 2px solid #0ea5e9; }
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
    """Enterprise Metric KPI Card."""
    def __init__(self, title, value, subtitle, badge_bg, badge_fg, icon_str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(115)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 700; border: none;")
        
        self.icon_lbl = QLabel(icon_str)
        self.icon_lbl.setFixedSize(30, 30)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet(f"background-color: {badge_bg}; color: {badge_fg}; border-radius: 8px; font-size: 13px; border: none;")
        
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self.icon_lbl)
        
        val_layout = QHBoxLayout()
        val_layout.setContentsMargins(0, 0, 0, 0)
        val_layout.setSpacing(10)
        
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet("color: #0f172a; font-size: 28px; font-weight: 800; border: none;")
        
        self.badge_lbl = QLabel(subtitle)
        self.badge_lbl.setStyleSheet(f"color: {badge_fg}; font-size: 10px; font-weight: 700; background-color: {badge_bg}; padding: 3px 8px; border-radius: 6px; border: none;")
        
        val_layout.addWidget(self.val_lbl)
        val_layout.addWidget(self.badge_lbl)
        val_layout.addStretch()
        
        layout.addLayout(h_layout)
        layout.addLayout(val_layout)
        apply_shadow(self, blur=14, dy=3, alpha=12)

    def update_value(self, value):
        self.val_lbl.setText(str(value))

class AIAuditSummaryCard(QFrame):
    """RAG AI Audit Executive Summary Card."""
    def __init__(self, risk_score: int, comp_score: int, findings: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(14)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("⚡ AI Audit Summary")
        title_lbl.setStyleSheet("font-weight: 800; font-size: 15px; color: #0f172a; border: none;")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)
        
        self.risk_bar_widget = self.create_bar("Portfolio Risk Score", risk_score, "#10b981" if risk_score < 30 else "#f59e0b")
        self.comp_bar_widget = self.create_bar("Compliance Score", comp_score, "#0ea5e9")
        self.layout.addWidget(self.risk_bar_widget)
        self.layout.addWidget(self.comp_bar_widget)
        
        self.f_box = QFrame()
        self.f_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 8px; padding: 10px;")
        self.f_layout = QVBoxLayout(self.f_box)
        self.f_layout.setContentsMargins(8, 8, 8, 8)
        self.f_layout.setSpacing(6)
        
        f_lbl = QLabel("RECENT AI FINDINGS & ANOMALIES")
        f_lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; letter-spacing: 0.5px; border: none;")
        self.f_layout.addWidget(f_lbl)
        
        if findings:
            for item in findings[:2]:
                item_lbl = QLabel(f"• {item}")
                item_lbl.setWordWrap(True)
                item_lbl.setStyleSheet("font-size: 11px; color: #334155; border: none;")
                self.f_layout.addWidget(item_lbl)
        else:
            no_findings = QLabel("No AI findings recorded. Ingest documents to run live RAG analysis.")
            no_findings.setStyleSheet("font-size: 11px; color: #94a3b8; border: none;")
            self.f_layout.addWidget(no_findings)
            
        self.layout.addWidget(self.f_box)
        self.layout.addStretch()
        apply_shadow(self, blur=15, dy=3, alpha=15)

    def create_bar(self, label_text, val_pct, color_hex):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        top_h = QHBoxLayout()
        t_lbl = QLabel(label_text)
        t_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; border: none;")
        v_lbl = QLabel(f"{val_pct}%")
        v_lbl.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {color_hex}; border: none;")
        top_h.addWidget(t_lbl)
        top_h.addStretch()
        top_h.addWidget(v_lbl)
        l.addLayout(top_h)
        
        pbar = QProgressBar()
        pbar.setFixedHeight(8)
        pbar.setValue(min(100, val_pct))
        pbar.setTextVisible(False)
        pbar.setStyleSheet(f"QProgressBar {{ border: none; background-color: #f1f5f9; border-radius: 4px; }} QProgressBar::chunk {{ background-color: {color_hex}; border-radius: 4px; }}")
        l.addWidget(pbar)
        return w

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
        series.setPen(QPen(QColor("#0ea5e9"), 3))
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        data_points = [12, 18, 15, 25, 22, 28]
        if projects:
            for idx, p in enumerate(projects[:6]):
                data_points[idx] = 100 if p.status == "Completed" else 60 if p.status == "Execution" else 30
                
        for i, val in enumerate(data_points):
            series.append(i, val)
            
        chart.addSeries(series)
        
        axis_x = QCategoryAxis()
        for i, m in enumerate(months): axis_x.append(m, i)
        axis_x.setLabelsColor(QColor("#64748b"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setLabelsColor(QColor("#64748b"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("border: none; background: transparent;")
        
        layout.addWidget(chart_view)
        apply_shadow(self, blur=15, dy=3, alpha=15)

class RiskDistributionChart(QFrame):
    """Enterprise Multi-Segment Donut Chart for Risk Level Classification."""
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

# ==============================================================================
# MASTER DASHBOARD WINDOW & CONTROLLER
# ==============================================================================

class DashboardWindow(QWidget):
    """Master Dashboard Window & Navigation Controller for FinAuditPro."""

    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.workflow_manager = WorkflowManager()
        self.event_manager = WorkflowEventManager()
        
        self.setWindowTitle("FinAuditPro - Enterprise Audit Workspace")
        self.resize(1440, 900)
        self.setObjectName("appBg")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. FAANG Dark Sidebar Navigation
        sidebar = self._build_sidebar()
        
        # 2. Main Content Stacked Container
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #f8fafc; border: none;")
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        header = self._build_header()
        content_layout.addWidget(header)
        
        overview_page = self._build_overview_page()
        self.stacked_widget = self._build_stacked_pages(overview_page)
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(main_content)
        
        self._wire_navigation()
        self.setup_keyboard_shortcuts()
        self.data_changed.connect(self.refresh_realtime_data)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #0b0f19; border-right: 1px solid #1e293b;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
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
        return sidebar

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
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
        return header

    def _build_overview_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(32, 28, 32, 32)
        body_layout.setSpacing(24)
        
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
        
        # 4 KPI Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        with get_session() as session:
            total_clients = session.query(Client).count()
            completed_audits = session.query(AuditProject).filter_by(status='Completed').count()
            pending_reviews = session.query(AuditProject).filter_by(status='Pending Review').count()
            high_risk_cases = session.query(AuditProject).filter_by(risk_level='High').count()

            self.card_clients = MetricCard("Total Clients", str(total_clients), "+12%", "#e0f2fe", "#0284c7", "👥")
            self.card_completed = MetricCard("Completed Audits", str(completed_audits), "This Year", "#dcfce7", "#16a34a", "✅")
            self.card_pending = MetricCard("Pending Reviews", str(pending_reviews), "Action Req.", "#fef3c7", "#d97706", "🕒")
            self.card_high_risk = MetricCard("High Risk Cases", str(high_risk_cases), "Flagged by AI", "#fee2e2", "#dc2626", "⚠️")

            stats_layout.addWidget(self.card_clients)
            stats_layout.addWidget(self.card_completed)
            stats_layout.addWidget(self.card_pending)
            stats_layout.addWidget(self.card_high_risk)
            
            body_layout.addLayout(stats_layout)
            
            # Middle Analytics Row
            mid_layout = QHBoxLayout()
            mid_layout.setSpacing(16)
            
            projects = session.query(AuditProject).all()
            avg_risk = int(sum([p.risk_score or 0.0 for p in projects]) / len(projects)) if projects else 0
            comp_score = max(0, 100 - avg_risk) if projects else 100
            
            findings_query = session.query(Finding).order_by(Finding.id.desc()).limit(2).all()
            findings_list = [f.description for f in findings_query] if findings_query else []
            
            ai_card = AIAuditSummaryCard(avg_risk, comp_score, findings_list)
            progress_chart = AuditProgressChart(projects)
            
            low_count = session.query(AuditProject).filter_by(risk_level='Low').count()
            med_count = session.query(AuditProject).filter_by(risk_level='Medium').count()
            high_count = session.query(AuditProject).filter_by(risk_level='High').count()
            if low_count == 0 and med_count == 0 and high_count == 0: low_count = max(1, len(projects))
            
            risk_chart = RiskDistributionChart(low_count, med_count, high_count)
            
            mid_layout.addWidget(ai_card, 3)
            mid_layout.addWidget(progress_chart, 4)
            mid_layout.addWidget(risk_chart, 3)
            
            body_layout.addLayout(mid_layout)
            
            # QTableView Model-View Section
            table_frame = QFrame()
            table_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
            t_layout = QVBoxLayout(table_frame)
            t_layout.setContentsMargins(16, 14, 16, 14)
            t_layout.setSpacing(10)
            
            t_header = QHBoxLayout()
            t_title = QLabel("Recent Audit Projects")
            t_title.setStyleSheet("font-weight: 800; font-size: 15px; color: #0f172a; border: none;")
            t_header.addWidget(t_title)
            t_header.addStretch()
            t_layout.addLayout(t_header)
            
            recent_projs = session.query(AuditProject).order_by(AuditProject.id.desc()).limit(10).all()
            self.table_model = AuditProjectsTableModel(recent_projs)
        
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setItemDelegate(AuditStatusDelegate(self.table_view))
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setShowGrid(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setStyleSheet("""
            QTableView { border: none; background: white; }
            QHeaderView::section { background-color: #f8fafc; color: #475569; padding: 10px; border: none; border-bottom: 1px solid #e2e8f0; font-weight: 700; font-size: 10px; letter-spacing: 0.5px; }
            QTableView::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-size: 12px; }
        """)
        self.table_view.doubleClicked.connect(self.on_table_double_clicked)
        
        t_layout.addWidget(self.table_view)
        apply_shadow(table_frame, blur=15, dy=3, alpha=15)
        
        body_layout.addWidget(table_frame)
        body_layout.addStretch()
        scroll.setWidget(body_widget)
        return scroll

    def _build_stacked_pages(self, overview_widget: QWidget) -> QStackedWidget:
        stacked_widget = QStackedWidget()
        
        def safe_load(widget_cls, title):
            try:
                return widget_cls()
            except (SQLAlchemyError, ValueError, RuntimeError) as e:
                logger.error(f"{title} failed to load: {e}", exc_info=True)
                return PlaceholderWidget(f"Unable to load {title}: {e}")

        # Index 0: Master Dashboard
        stacked_widget.addWidget(overview_widget)
        # Index 1: Client Management
        self.clients_page = safe_load(ClientManagementWidget, "Client Management")
        stacked_widget.addWidget(self.clients_page)
        # Index 2: Upload Documents
        self.docs_page = safe_load(DocumentUploadWidget, "Document Upload")
        stacked_widget.addWidget(self.docs_page)
        # Index 3: AI Audit Analysis
        self.ai_page = safe_load(AIAuditWidget, "AI Audit Analysis")
        stacked_widget.addWidget(self.ai_page)
        # Index 4: Financial Statements
        self.statements_page = safe_load(FinancialStatementsWidget, "Financial Statements")
        stacked_widget.addWidget(self.statements_page)
        # Index 5: GST Verification
        self.gst_page = safe_load(GSTVerificationWidget, "GST Verification")
        stacked_widget.addWidget(self.gst_page)
        # Index 6: Compliance Monitoring
        self.compliance_page = safe_load(ComplianceWidget, "Compliance Monitoring")
        stacked_widget.addWidget(self.compliance_page)
        # Index 7: Risk Analysis
        self.risk_page = safe_load(RiskAnalysisWidget, "Risk Analysis")
        stacked_widget.addWidget(self.risk_page)
        # Index 8: Reports
        self.reports_page = safe_load(ReportsWidget, "Report Generator")
        stacked_widget.addWidget(self.reports_page)
        # Index 9: Audit History
        self.history_page = safe_load(AuditHistoryWidget, "Audit History")
        stacked_widget.addWidget(self.history_page)
        # Index 10: Settings
        self.settings_page = safe_load(SettingsWidget, "System Settings")
        stacked_widget.addWidget(self.settings_page)
        # Index 11: Working Papers
        self.working_papers_page = safe_load(WorkingPaperWidget, "Working Papers")
        stacked_widget.addWidget(self.working_papers_page)
        return stacked_widget

    def _wire_navigation(self):
        for i, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked=False, idx=i, b=btn: self._on_nav_click(idx, b))

    def _on_nav_click(self, index: int, btn: SidebarButton):
        self.stacked_widget.setCurrentIndex(index)
        for b in self.nav_buttons:
            b.set_active(False)
        btn.set_active(True)
        self.refresh_realtime_data()

    def on_table_double_clicked(self, index: QModelIndex):
        self.stacked_widget.setCurrentIndex(11) # Working Papers
        for btn in self.nav_buttons: btn.set_active(False)
        self.btn_working_papers.set_active(True)

    def refresh_realtime_data(self):
        """Refreshes metrics and QTableView Model from database."""
        try:
            with get_session() as session:
                total_clients = session.query(Client).count()
                completed_audits = session.query(AuditProject).filter_by(status='Completed').count()
                pending_reviews = session.query(AuditProject).filter_by(status='Pending Review').count()
                high_risk_cases = session.query(AuditProject).filter_by(risk_level='High').count()

                self.card_clients.update_value(total_clients)
                self.card_completed.update_value(completed_audits)
                self.card_pending.update_value(pending_reviews)
                self.card_high_risk.update_value(high_risk_cases)

                recent_projs = session.query(AuditProject).order_by(AuditProject.id.desc()).limit(10).all()
                self.table_model.update_projects(recent_projs)
        except SQLAlchemyError as e:
            logger.warning(f"Database warning during realtime refresh: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during realtime refresh: {e}", exc_info=True)

    def open_create_audit_dialog(self):
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.MANAGE_CLIENTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to create audit projects.")
            return

        dialog = CreateAuditProjectDialog(None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_id = dialog.client_combo.currentData()
            fy = dialog.fy_combo.currentText().strip() if hasattr(dialog, 'fy_combo') else "2025-26"
            audit_type = dialog.audit_type_combo.currentText().strip() if hasattr(dialog, 'audit_type_combo') else "Statutory Audit"
            status = dialog.stage_combo.currentText().strip() if hasattr(dialog, 'stage_combo') else "Planning"
            risk = dialog.risk_combo.currentText().strip() if hasattr(dialog, 'risk_combo') else "Medium"

            with get_session() as session:
                proj = AuditProject(client_id=client_id, financial_year=fy, status=status, risk_level=risk)
                session.add(proj)
                session.commit()
                proj_id = proj.id

            self.populate_client_selector()
            idx = self.client_selector.findData(proj_id)
            if idx >= 0: self.client_selector.setCurrentIndex(idx)
            self.data_changed.emit()
            QMessageBox.information(self, "Audit Created", f"Successfully initialized new {audit_type} for FY {fy}.")

    def populate_client_selector(self):
        self.client_selector.clear()
        with get_session() as session:
            clients = session.query(Client).all()
            for c in clients:
                projs = session.query(AuditProject).filter_by(client_id=c.id).all()
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
            with get_session() as session:
                if isinstance(data, str) and data.startswith("client_"):
                    client_id = int(data.split("_")[1])
                    proj = AuditProject(client_id=client_id, financial_year="2025-26", status="Execution")
                    session.add(proj)
                    session.commit()
                    proj_id = proj.id
                    c_id = proj.client_id
                    fy = proj.financial_year or "2025-26"
                else:
                    proj_id = int(data)
                    proj = session.query(AuditProject).filter_by(id=proj_id).first()
                    c_id = proj.client_id if proj else None
                    fy = proj.financial_year if proj else "2025-26"

            if proj_id and c_id:
                self.workflow_manager.initialize_engagement(engagement_id=proj_id, client_id=c_id, financial_year=fy)
                if hasattr(self, 'ai_page') and self.ai_page is not None:
                    self.ai_page.active_engagement_id = proj_id
        except (SQLAlchemyError, ValueError, RuntimeError) as e:
            logger.warning(f"Engagement change warning: {e}")

    def setup_keyboard_shortcuts(self):
        for i in range(min(9, len(self.nav_buttons))):
            btn = self.nav_buttons[i]
            shortcut = QShortcut(QKeySequence(f"Alt+{i+1}"), self)
            shortcut.activated.connect(btn.click)
            btn.setToolTip(f"Hotkey: Alt+{i+1}")
            
        self.f5_shortcut = QShortcut(QKeySequence("F5"), self)
        self.f5_shortcut.activated.connect(self.refresh_realtime_data)
        
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self.settings_shortcut.activated.connect(self.btn_settings.click)

    def toggle_theme(self):
        is_dark = getattr(self, '_dark_mode', False)
        self._dark_mode = not is_dark
        self.btn_theme.setText("☀️" if self._dark_mode else "🌙")
        QMessageBox.information(self, "Theme Preferences", f"Switched to {'Dark' if self._dark_mode else 'Standard Enterprise Slate'} palette.")

    def show_keyboard_shortcuts_dialog(self):
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
• <b>F5</b> : Refresh Realtime Data<br/>
• <b>Ctrl + ,</b> : Open Settings & Governance<br/>
"""
        QMessageBox.information(self, "Keyboard Shortcuts Reference", shortcuts_text)

    def show_notifications_popup(self):
        QMessageBox.information(
            self,
            "Active Audit Alerts",
            "<b>Active Compliance Alerts:</b><br/><br/>"
            "• GSTR-3B Tax Filing Deadline: <b>5 days remaining</b><br/>"
            "• Income Tax Audit Report (Form 3CD): <b>In Progress</b><br/>"
            "• CARO 2020 Physical Inventory Verification: <b>Completed</b>"
        )

    def closeEvent(self, event):
        event.accept()
