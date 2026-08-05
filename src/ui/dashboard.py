"""
Enterprise Dashboard Module for FinAuditPro.
Redesigned with Model-View Architecture (QAbstractTableModel + QTableView + QStyledItemDelegate),
Real-Time Signal/Slot Automatic Data Refresh, QtCharts QSplineSeries & QPieSeries,
and RAG AI Executive Summary Card with Trustworthy Light Sky Blue UI Design.
"""

import os
import logging
from datetime import datetime
from typing import List, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout, 
                               QTableView, QHeaderView, QStackedWidget, QLineEdit, 
                               QComboBox, QProgressBar, QMenu, QStyledItemDelegate,
                               QStyleOptionViewItem, QMessageBox, QDialog, QStyle)
from PySide6.QtCore import Qt, QSize, Slot, QAbstractTableModel, QModelIndex, QRect, Signal, QMargins, QTimer
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

class PlaceholderWidget(QWidget):
    """Fallback widget displayed when a stacked page fails to load."""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        error_widget = ErrorStateWidget("Page Load Error", message)
        layout.addWidget(error_widget)

# ==============================================================================
# MODEL-VIEW ARCHITECTURE (QAbstractTableModel + QStyledItemDelegate)
# ==============================================================================

class AuditProjectsTableModel(QAbstractTableModel):
    """Real-time Table Model for Audit Projects storing detached values safely."""
    
    HEADERS = ["CLIENT NAME", "AUDIT TYPE", "STATUS", "RISK LEVEL", "LAST UPDATED"]
    
    def __init__(self, projects: List[Any] = None, parent=None):
        super().__init__(parent)
        self._client_cache = {}
        self._projects = self._normalize(projects or [])
        self._load_client_cache()

    def _load_client_cache(self):
        client_ids = {p.get('client_id') for p in getattr(self, '_projects', []) if p.get('client_id')}
        with get_session() as session:
            ds = DashboardService(session)
            self._client_cache = ds.load_client_name_cache(client_ids)

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
                return f" {client_name}"
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

        # Row background selection highlight
        if bool(option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(rect, QColor("#e0f2fe"))
        elif index.row() % 2 == 1:
            painter.fillRect(rect, QColor("#f8fafc"))
        else:
            painter.fillRect(rect, QColor("#ffffff"))

        if col == 2: # Status Pill
            if "Active" in text or "Execution" in text:
                bg_color = QColor("#e0f2fe")
                text_color = QColor("#0284c7")
            elif "Completed" in text:
                bg_color = QColor("#dcfce7")
                text_color = QColor("#16a34a")
            else:
                bg_color = QColor("#fef3c7")
                text_color = QColor("#d97706")
            
            pill_rect = rect.adjusted(12, 6, -12, -6)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(pill_rect, 6, 6)
            
            painter.setPen(QPen(text_color))
            painter.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, text)

        elif col == 3: # Risk Dot & Text
            dot_color = QColor("#16a34a") if "Low" in text else QColor("#d97706") if "Medium" in text else QColor("#dc2626")
            
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

from .icons import get_app_icon, get_app_pixmap

class SidebarButton(QPushButton):
    """Modern Enterprise Sidebar Button with active indicator tab & SVG QIcon."""
    def __init__(self, text, icon_name="", is_active=False, parent=None):
        super().__init__(parent)
        self.setObjectName("navButton")
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(f"  {text}")
        if icon_name:
            self.setIcon(get_app_icon(icon_name, color="#0284c7" if is_active else "#64748b", size=18))
            self.setIconSize(QSize(18, 18))
        self.set_active(is_active)

    def set_active(self, is_active: bool):
        self.setProperty("active", "true" if is_active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

class GlobalSearchWidget(QFrame):
    """Global Desktop Search Bar with K hotkey badge & real-time popup results."""
    result_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 36)
        self.setObjectName("globalSearchFrame")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)
        
        search_icon = QLabel("")
        search_icon.setObjectName("globalSearchIcon")
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Search clients, reports, documents... (Ctrl+K)")
        self.input_field.setObjectName("globalSearchInput")
        self.input_field.textChanged.connect(self._on_search_text_changed)
        
        shortcut_lbl = QLabel("K")
        shortcut_lbl.setObjectName("globalShortcutBadge")
        
        layout.addWidget(search_icon)
        layout.addWidget(self.input_field)
        layout.addWidget(shortcut_lbl)

        self.menu = QMenu(self)
        self.menu.setObjectName("globalSearchMenu")

    def _on_search_text_changed(self, text: str):
        text = text.strip()
        self.menu.clear()
        if len(text) < 2:
            self.menu.hide()
            return

        try:
            with get_session() as session:
                ds = DashboardService(session)
                clients, findings = ds.search_clients_and_findings(text)

                if clients:
                    header = self.menu.addAction(" CLIENTS")
                    header.setEnabled(False)
                    for c in clients:
                        action = self.menu.addAction(f"   {c.name}")
                        action.triggered.connect(lambda checked=False, page=1: self.result_selected.emit(page))

                if findings:
                    header2 = self.menu.addAction(" FINDINGS & REPORTS")
                    header2.setEnabled(False)
                    for f in findings:
                        desc = f.description[:40] + "..." if len(f.description) > 40 else f.description
                        action = self.menu.addAction(f"   {desc}")
                        action.triggered.connect(lambda checked=False, page=8: self.result_selected.emit(page))

                if not clients and not findings:
                    no_res = self.menu.addAction("No matching records found")
                    no_res.setEnabled(False)

            self.menu.popup(self.mapToGlobal(self.rect().bottomLeft()))
        except Exception:
            pass

class MetricCard(QFrame):
    """Apple macOS Minimalist KPI Metric Card."""
    def __init__(self, title, value, subtitle, badge_bg, badge_fg, accent_hex="#007aff", icon_str="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(115)
        self.setObjectName("metricCard")
        self.setStyleSheet("""
            QFrame#metricCard {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 14px;
            }
            QFrame#metricCard:hover {
                border-color: #d1d1d6;
                background-color: #fafafa;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        # Uppercase subtle tracking label
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet("color: #86868b; font-size: 11px; font-weight: 600; border: none; letter-spacing: 0.6px;")
        
        self.badge_lbl = QLabel(subtitle)
        self.badge_lbl.setStyleSheet(
            f"color: {badge_fg}; font-size: 11px; font-weight: 600; "
            f"background-color: {badge_bg}; padding: 3px 9px; border-radius: 6px; border: none;"
        )
        
        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self.badge_lbl)
        
        val_layout = QHBoxLayout()
        val_layout.setContentsMargins(0, 0, 0, 0)
        
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet("font-size: 34px; font-weight: 600; color: #1d1d1f; border: none; letter-spacing: -0.6px;")
        
        val_layout.addWidget(self.val_lbl)
        val_layout.addStretch()
        
        layout.addLayout(h_layout)
        layout.addLayout(val_layout)
        apply_shadow(self, blur=16, dx=0, dy=2, alpha=8)

    def update_value(self, value):
        self.val_lbl.setText(str(value))

class AIAuditSummaryCard(QFrame):
    """RAG AI Audit Executive Summary Card — Apple Minimalist split layout."""
    def __init__(self, risk_score: int, comp_score: int, findings: list, parent=None):
        super().__init__(parent)
        self.setObjectName("aiSummaryCard")
        self.setStyleSheet("""
            QFrame#aiSummaryCard {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 14px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(14)
        
        # Header
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("AI Audit Summary")
        title_lbl.setStyleSheet("font-weight: 600; font-size: 15px; color: #1d1d1f; border: none;")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)
        
        # Content Split: Left Scores, Right Findings
        body_split = QHBoxLayout()
        body_split.setContentsMargins(0, 0, 0, 0)
        body_split.setSpacing(14)
        
        # Left Panel — Scores
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #f5f5f7; border: 1px solid #e5e5ea; border-radius: 10px;")
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.setContentsMargins(14, 12, 14, 12)
        lp_layout.setSpacing(10)
        
        self.risk_bar_widget = self.create_bar("Portfolio Risk", risk_score, "#ff9500" if risk_score > 20 else "#34c759")
        self.comp_bar_widget = self.create_bar("Compliance Score", comp_score, "#007aff")
        lp_layout.addWidget(self.risk_bar_widget)
        lp_layout.addWidget(self.comp_bar_widget)
        
        # Right Panel — Findings
        self.f_box = QFrame()
        self.f_box.setStyleSheet("background-color: #f5f5f7; border: 1px solid #e5e5ea; border-radius: 10px;")
        self.f_layout = QVBoxLayout(self.f_box)
        self.f_layout.setContentsMargins(14, 12, 14, 12)
        self.f_layout.setSpacing(8)
        
        f_lbl = QLabel("RECENT AI FINDINGS")
        f_lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #86868b; letter-spacing: 0.8px; border: none;")
        self.f_layout.addWidget(f_lbl)
        
        if findings:
            for item in findings[:2]:
                row = QHBoxLayout()
                row.setSpacing(6)
                dot = QLabel("●")
                dot.setStyleSheet("color: #ff9500; font-size: 8px; border: none;")
                item_lbl = QLabel(str(item))
                item_lbl.setWordWrap(True)
                item_lbl.setStyleSheet("font-size: 12px; color: #1d1d1f; border: none;")
                row.addWidget(dot)
                row.addWidget(item_lbl, stretch=1)
                self.f_layout.addLayout(row)
        else:
            no_findings = QLabel("No anomalies detected. Ingest audit documents to activate RAG analysis.")
            no_findings.setStyleSheet("font-size: 12px; color: #6e6e73; border: none;")
            no_findings.setWordWrap(True)
            self.f_layout.addWidget(no_findings)
            
        body_split.addWidget(left_panel, 1)
        body_split.addWidget(self.f_box, 1)
        
        self.layout.addLayout(body_split)
        apply_shadow(self, blur=16, dx=0, dy=2, alpha=8)

    def create_bar(self, label_text, val_pct, color_hex):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        top_h = QHBoxLayout()
        t_lbl = QLabel(label_text)
        t_lbl.setStyleSheet("font-size: 11px; color: #6e6e73; font-weight: 500; border: none;")
        v_lbl = QLabel(f"{val_pct}%")
        v_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {color_hex}; border: none;")
        top_h.addWidget(t_lbl)
        top_h.addStretch()
        top_h.addWidget(v_lbl)
        l.addLayout(top_h)
        
        pbar = QProgressBar()
        pbar.setFixedHeight(5)
        pbar.setValue(min(100, val_pct))
        pbar.setTextVisible(False)
        pbar.setStyleSheet(f"QProgressBar {{ border: none; background-color: #e5e5ea; border-radius: 2px; }} QProgressBar::chunk {{ background-color: {color_hex}; border-radius: 2px; }}")
        l.addWidget(pbar)
        return w

class AuditProgressChart(QFrame):
    """Apple macOS Spline Line Chart for Audit Trends."""
    def __init__(self, projects: list, parent=None):
        super().__init__(parent)
        self.setObjectName("auditProgressCard")
        self.setStyleSheet("""
            QFrame#auditProgressCard {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 14px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("Audit Progress Trend")
        title_lbl.setStyleSheet("font-weight: 600; font-size: 15px; color: #1d1d1f; border: none;")
        
        period_combo = QComboBox()
        period_combo.addItems(["Last 6 Months", "FY 2025-26", "All Time"])
        period_combo.setFixedWidth(130)
        period_combo.setObjectName("periodCombo")
        
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(period_combo)
        layout.addLayout(h_layout)
        
        chart = QChart()
        chart.legend().hide()
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(4, 4, 4, 4))
        
        series = QSplineSeries()
        series.setPen(QPen(QColor("#007aff"), 3))
        
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
        axis_x.setLabelsColor(QColor("#86868b"))
        axis_x.setGridLineColor(QColor("#f2f2f7"))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setLabelsColor(QColor("#86868b"))
        axis_y.setGridLineColor(QColor("#f2f2f7"))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setObjectName("transparentChartView")
        
        layout.addWidget(chart_view)
        apply_shadow(self, blur=16, dx=0, dy=2, alpha=8)

class RiskDistributionChart(QFrame):
    """Apple macOS Donut Chart for Risk Level Classification."""
    def __init__(self, low: int, med: int, high: int, parent=None):
        super().__init__(parent)
        self.setObjectName("riskDistributionCard")
        self.setStyleSheet("""
            QFrame#riskDistributionCard {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 14px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        
        title_lbl = QLabel("Risk Distribution")
        title_lbl.setStyleSheet("font-weight: 600; font-size: 15px; color: #1d1d1f; border: none;")
        layout.addWidget(title_lbl)
        
        chart = QChart()
        chart.legend().hide()
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))
        
        total_val = low + med + high
        if total_val > 0:
            pie_series = QPieSeries()
            pie_series.setHoleSize(0.65)
            
            if low > 0:
                s1 = pie_series.append("Low Risk", low)
                s1.setBrush(QColor("#34c759"))
            if med > 0:
                s2 = pie_series.append("Medium Risk", med)
                s2.setBrush(QColor("#ff9500"))
            if high > 0:
                s3 = pie_series.append("High Risk", high)
                s3.setBrush(QColor("#ff3b30"))
            
            chart.addSeries(pie_series)
            
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            chart_view.setObjectName("transparentChartView")
            
            center_lbl = QLabel(f"<b style='font-size:20px; color:#1d1d1f;'>{total_val}</b><br/><span style='color:#86868b; font-size:10px;'>Total Audits</span>", chart_view)
            center_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            center_lbl.setObjectName("donutCenterLabel")
            
            overlay = QVBoxLayout(chart_view)
            overlay.addWidget(center_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(chart_view)
        else:
            empty_lbl = QLabel("No Risk Data — Upload documents to begin analysis")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #86868b; font-size: 12px; font-weight: 500; border: none; padding: 24px;")
            layout.addWidget(empty_lbl)
        
        leg_layout = QHBoxLayout()
        leg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leg_layout.setSpacing(14)
        
        def create_leg_item(color_hex, label_text):
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(4)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color_hex}; font-size: 8px; border: none;")
            txt = QLabel(label_text)
            txt.setStyleSheet("color: #6e6e73; font-size: 11px; font-weight: 500; border: none;")
            l.addWidget(dot)
            l.addWidget(txt)
            return w
            
        leg_layout.addWidget(create_leg_item("#34c759", "Low Risk"))
        leg_layout.addWidget(create_leg_item("#ff9500", "Medium Risk"))
        leg_layout.addWidget(create_leg_item("#ff3b30", "High Risk"))
        layout.addLayout(leg_layout)
        
        apply_shadow(self, blur=16, dx=0, dy=2, alpha=8)

# ==============================================================================
# MASTER DASHBOARD WINDOW & CONTROLLER
# ==============================================================================

class DashboardWindow(QWidget):
    """Master Dashboard Window & Navigation Controller for FinAuditPro."""

    data_changed = Signal()

    def __init__(self, user=None):
        super().__init__()
        self.current_user = user
        self.workflow_manager = WorkflowManager()
        self.event_manager = WorkflowEventManager()
        
        self.setWindowTitle("FinAuditPro - Enterprise Audit Workspace")
        self.resize(1440, 900)
        self.setObjectName("appBg")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Clean Light Sidebar Navigation
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

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_initial_data_loaded', False):
            self._initial_data_loaded = True
            QTimer.singleShot(0, self.refresh_realtime_data)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setObjectName("dashboardSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        logo_container = QFrame()
        logo_container.setFixedHeight(70)
        logo_container.setObjectName("sidebarLogoContainer")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 0, 20, 0)
        
        logo_badge = QLabel("FA")
        logo_badge.setFixedSize(32, 32)
        logo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_badge.setObjectName("sidebarLogoBadge")
        
        app_title = QLabel("FinAuditPro")
        app_title.setObjectName("sidebarAppTitle")
        logo_layout.addWidget(logo_badge)
        logo_layout.addSpacing(10)
        logo_layout.addWidget(app_title)
        logo_layout.addStretch()
        sidebar_layout.addWidget(logo_container)
        
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setObjectName("sidebarNavScroll")
        nav_widget = QWidget()
        nav_widget.setObjectName("sidebarNavWidget")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)
        
        def add_section_label(text):
            lbl = QLabel(text)
            lbl.setObjectName("sidebarSectionLabel")
            nav_layout.addWidget(lbl)
            
        add_section_label("MAIN MENU")
        self.btn_dashboard = SidebarButton("Dashboard", "dashboard", True)
        self.btn_clients = SidebarButton("Client Management", "clients")
        self.btn_upload = SidebarButton("Upload Documents", "documents")
        nav_layout.addWidget(self.btn_dashboard)
        nav_layout.addWidget(self.btn_clients)
        nav_layout.addWidget(self.btn_upload)
        
        add_section_label("AUDIT WORKSPACE")
        self.btn_ai = SidebarButton("AI Audit Analysis", "ai")
        self.btn_statements = SidebarButton("Financial Statements", "statements")
        self.btn_gst = SidebarButton("GST Verification", "check")
        self.btn_compliance = SidebarButton("Compliance Monitoring", "compliance")
        self.btn_risk = SidebarButton("Risk Analysis", "risk")
        self.btn_working_papers = SidebarButton("Working Papers", "papers")
        nav_layout.addWidget(self.btn_ai)
        nav_layout.addWidget(self.btn_statements)
        nav_layout.addWidget(self.btn_gst)
        nav_layout.addWidget(self.btn_compliance)
        nav_layout.addWidget(self.btn_risk)
        nav_layout.addWidget(self.btn_working_papers)

        add_section_label("SETTINGS & LOGS")
        self.btn_reports = SidebarButton("Reports", "reports")
        self.btn_history = SidebarButton("Audit History", "history")
        self.btn_settings = SidebarButton("Settings", "settings")
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
        profile_frame.setObjectName("sidebarProfileFrame")
        profile_layout = QHBoxLayout(profile_frame)
        profile_layout.setContentsMargins(16, 0, 16, 0)
        
        display_name = self.current_user.username if self.current_user and getattr(self.current_user, 'username', None) else "admin"
        display_role = self.current_user.role if self.current_user and getattr(self.current_user, 'role', None) else "Audit Partner"
        avatar_text = display_name[:2].upper() if display_name else "AD"

        avatar_lbl = QLabel(avatar_text)
        avatar_lbl.setFixedSize(34, 34)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setObjectName("userAvatar")
        
        profile_info = QVBoxLayout()
        profile_info.setSpacing(2)
        profile_info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        name_lbl = QLabel(display_name)
        name_lbl.setObjectName("userName")
        role_lbl = QLabel(display_role)
        role_lbl.setObjectName("userRole")
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
        header.setObjectName("dashboardHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        self.search_bar = GlobalSearchWidget()
        self.search_bar.result_selected.connect(self._on_search_result_selected)
        header_layout.addWidget(self.search_bar)
        
        header_layout.addSpacing(20)
        header_layout.addWidget(QLabel("<b style='color:#0f172a;'>Active Audit:</b>"))
        self.client_selector = QComboBox()
        self.client_selector.setFixedWidth(220)
        self.client_selector.setObjectName("clientSelectorCombo")
        self.populate_client_selector()
        self.client_selector.currentIndexChanged.connect(self.on_active_engagement_changed)
        header_layout.addWidget(self.client_selector)
        
        btn_new_audit = QPushButton(" + New Audit")
        btn_new_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_audit.setObjectName("primaryBtn")
        btn_new_audit.clicked.connect(self.open_create_audit_dialog)
        header_layout.addWidget(btn_new_audit)
        
        header_layout.addStretch()
        
        
        self.btn_help = QPushButton("")
        self.btn_help.setFixedSize(34, 34)
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setObjectName("iconToolBtn")
        self.btn_help.clicked.connect(self.show_keyboard_shortcuts_dialog)

        self.btn_notif = QPushButton("")
        self.btn_notif.setFixedSize(34, 34)
        self.btn_notif.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_notif.setObjectName("iconToolBtn")
        self.btn_notif.clicked.connect(self.show_notifications_popup)


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
        body_layout.setContentsMargins(28, 24, 28, 28)
        body_layout.setSpacing(20)
        
        # Greeting Header Strip — Apple Minimalist Header
        hero_frame = QFrame()
        hero_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 14px;
                padding: 16px 20px;
            }
        """)
        hero_h = QHBoxLayout(hero_frame)
        hero_h.setContentsMargins(0, 0, 0, 0)
        
        hero_v = QVBoxLayout()
        hero_v.setSpacing(3)
        
        user_name = self.current_user.username.title() if self.current_user and getattr(self.current_user, 'username', None) else "Auditor"
        _hour = datetime.now().hour
        _greeting = "Good Morning" if _hour < 12 else "Good Afternoon" if _hour < 17 else "Good Evening"
        hero_title = QLabel(f"{_greeting}, {user_name}")
        hero_title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f; border: none; letter-spacing: -0.5px;")
        hero_sub = QLabel("Here is your statutory audit portfolio overview and AI risk assessment for today.")
        hero_sub.setStyleSheet("font-size: 13px; color: #6e6e73; border: none;")
        
        hero_v.addWidget(hero_title)
        hero_v.addWidget(hero_sub)
        
        date_lbl = QLabel(datetime.now().strftime("%A, %d %b %Y"))
        date_lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #6e6e73; background: #f5f5f7; padding: 6px 14px; border-radius: 8px; border: 1px solid #e5e5ea;")
        
        hero_h.addLayout(hero_v)
        hero_h.addStretch()
        hero_h.addWidget(date_lbl)
        
        body_layout.addWidget(hero_frame)
        apply_shadow(hero_frame, blur=16, dx=0, dy=2, alpha=8)
        
        # 4 KPI Cards Row with Apple macOS Color Tokens
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.card_clients = MetricCard("Total Clients", "0", "+12%", "#e8f2ff", "#007aff", "#007aff", "clients")
        self.card_completed = MetricCard("Completed Audits", "0", "This Year", "#eafff0", "#34c759", "#34c759", "check")
        self.card_pending = MetricCard("Pending Reviews", "0", "Action Req.", "#fff8e6", "#ff9500", "#ff9500", "risk")
        self.card_high_risk = MetricCard("High Risk Cases", "0", "Flagged by AI", "#ffebeb", "#ff3b30", "#ff3b30", "shield")

        stats_layout.addWidget(self.card_clients)
        stats_layout.addWidget(self.card_completed)
        stats_layout.addWidget(self.card_pending)
        stats_layout.addWidget(self.card_high_risk)
        
        body_layout.addLayout(stats_layout)

        # Welcome / onboarding banner — Apple Glass/Acrylic Card
        self.welcome_banner = QFrame()
        self.welcome_banner.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 14px;
            }
        """)
        wb_layout = QHBoxLayout(self.welcome_banner)
        wb_layout.setContentsMargins(20, 16, 20, 16)
        wb_layout.setSpacing(16)
        
        wb_text_v = QVBoxLayout()
        wb_text_v.setSpacing(3)
        wb_title = QLabel("Welcome to FinAuditPro Workspace")
        wb_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #1d1d1f; border: none;")
        wb_sub = QLabel("No active audit engagements or clients registered yet. Start by adding a client to set up statutory audits.")
        wb_sub.setStyleSheet("font-size: 13px; color: #6e6e73; border: none;")
        wb_sub.setWordWrap(True)
        wb_text_v.addWidget(wb_title)
        wb_text_v.addWidget(wb_sub)
        
        btn_add_client = QPushButton("+ Add First Client")
        btn_add_client.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_client.setObjectName("primaryBtn")
        btn_add_client.setStyleSheet("""
            QPushButton#primaryBtn {
                background-color: #007aff;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 18px;
                border: none;
            }
            QPushButton#primaryBtn:hover { background-color: #0062cc; }
        """)
        btn_add_client.clicked.connect(lambda: self.btn_clients.click())

        wb_layout.addLayout(wb_text_v, 1)
        wb_layout.addWidget(btn_add_client)
        self.welcome_banner.hide()  # hidden by default; shown if 0 clients
        body_layout.addWidget(self.welcome_banner)
        apply_shadow(self.welcome_banner, blur=16, dx=0, dy=2, alpha=8)
        
        # Middle Analytics Row
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(16)
        
        ai_card = AIAuditSummaryCard(0, 100, [])
        progress_chart = AuditProgressChart([])
        risk_chart = RiskDistributionChart(1, 0, 0)
        
        mid_layout.addWidget(ai_card, 3)
        mid_layout.addWidget(progress_chart, 4)
        mid_layout.addWidget(risk_chart, 3)
        
        body_layout.addLayout(mid_layout)
        
        # QTableView Model-View Section — Apple Table Container
        table_frame = QFrame()
        table_frame.setObjectName("recentProjectsTableFrame")
        table_frame.setStyleSheet("""
            QFrame#recentProjectsTableFrame {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 14px;
            }
        """)
        t_layout = QVBoxLayout(table_frame)
        t_layout.setContentsMargins(20, 18, 20, 18)
        t_layout.setSpacing(12)
        
        t_header = QHBoxLayout()
        t_title = QLabel("Recent Audit Projects")
        t_title.setStyleSheet("font-weight: 600; font-size: 15px; color: #1d1d1f; border: none;")
        t_header.addWidget(t_title)
        t_header.addStretch()
        t_layout.addLayout(t_header)
        
        self.table_model = AuditProjectsTableModel([])
        
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
        self.table_view.setObjectName("recentProjectsTableView")
        self.table_view.doubleClicked.connect(self.on_table_double_clicked)
        
        t_layout.addWidget(self.table_view)
        apply_shadow(table_frame, blur=15, dy=3, alpha=15)
        
        body_layout.addWidget(table_frame)
        body_layout.addStretch()
        scroll.setWidget(body_widget)
        return scroll

    def _build_stacked_pages(self, overview_widget: QWidget) -> QStackedWidget:
        self._page_classes = {
            1: (ClientManagementWidget, "Client Management"),
            2: (DocumentUploadWidget, "Document Upload"),
            3: (AIAuditWidget, "AI Audit Analysis"),
            4: (FinancialStatementsWidget, "Financial Statements"),
            5: (GSTVerificationWidget, "GST Verification"),
            6: (ComplianceWidget, "Compliance Monitoring"),
            7: (RiskAnalysisWidget, "Risk Analysis"),
            8: (ReportsWidget, "Report Generator"),
            9: (AuditHistoryWidget, "Audit History"),
            10: (SettingsWidget, "System Settings"),
            11: (WorkingPaperWidget, "Working Papers"),
        }
        self._loaded_pages = {0: True}
        stacked_widget = QStackedWidget()
        stacked_widget.addWidget(overview_widget)

        for i in range(1, 12):
            dummy = QWidget()
            stacked_widget.addWidget(dummy)

        return stacked_widget

    def _wire_navigation(self):
        for i, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked=False, idx=i, b=btn: self._on_nav_click(idx, b))

    def _ensure_page_loaded(self, index: int):
        if index in self._page_classes and not self._loaded_pages.get(index, False):
            widget_cls, title = self._page_classes[index]
            try:
                widget = widget_cls()
            except (SQLAlchemyError, ValueError, RuntimeError) as e:
                logger.error(f"{title} failed to load: {e}", exc_info=True)
                widget = PlaceholderWidget(f"Unable to load {title}: {e}")
            
            old_w = self.stacked_widget.widget(index)
            self.stacked_widget.removeWidget(old_w)
            old_w.deleteLater()
            self.stacked_widget.insertWidget(index, widget)
            self._loaded_pages[index] = True
            
            attr_map = {
                1: 'clients_page', 2: 'docs_page', 3: 'ai_page', 4: 'statements_page',
                5: 'gst_page', 6: 'compliance_page', 7: 'risk_page', 8: 'reports_page',
                9: 'history_page', 10: 'settings_page', 11: 'working_papers_page'
            }
            if index in attr_map:
                setattr(self, attr_map[index], widget)

    def _setup_search_shortcut(self):
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(lambda: self.search_bar.input_field.setFocus())

    def _on_nav_click(self, index: int, btn: SidebarButton):
        self._ensure_page_loaded(index)
        self.stacked_widget.setCurrentIndex(index)
        for b in self.nav_buttons:
            b.set_active(False)
        btn.set_active(True)
        self.refresh_realtime_data()

    def _on_search_result_selected(self, page_index: int):
        self._ensure_page_loaded(page_index)
        self.stacked_widget.setCurrentIndex(page_index)
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == page_index)

    def on_table_double_clicked(self, index: QModelIndex):
        self._ensure_page_loaded(11) # Working Papers
        self.stacked_widget.setCurrentIndex(11)
        for btn in self.nav_buttons: btn.set_active(False)
        self.btn_working_papers.set_active(True)

    def refresh_realtime_data(self):
        """Refreshes metrics and QTableView Model from database via DashboardService."""
        try:
            with get_session() as session:
                ds = DashboardService(session)
                metrics = ds.get_realtime_metrics()

                self.card_clients.update_value(metrics["total_clients"])
                self.card_completed.update_value(metrics["completed_audits"])
                self.card_pending.update_value(metrics["pending_reviews"])
                self.card_high_risk.update_value(metrics["high_risk_cases"])
                self.table_model.update_projects(metrics["recent_projects"])

                # Show welcome banner only on a truly fresh/empty database
                if hasattr(self, 'welcome_banner'):
                    is_empty = metrics["total_clients"] == 0
                    self.welcome_banner.setVisible(is_empty)
        except SQLAlchemyError as e:
            logger.warning(f"Database warning during realtime refresh: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during realtime refresh: {e}", exc_info=True)

    def open_create_audit_dialog(self):
        sm = SecurityManager()
        if not sm.current_session or not sm.check_permission(Permission.MANAGE_CLIENTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to create audit projects.")
            return

        from database.database import get_session
        with get_session() as session:
            dialog = CreateAuditProjectDialog(session, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                client_id = dialog.client_combo.currentData()
                fy = dialog.fy_combo.currentText().strip() if hasattr(dialog, 'fy_combo') else "2025-26"
                audit_type = dialog.audit_type_combo.currentText().strip() if hasattr(dialog, 'audit_type_combo') else "Statutory Audit"
                status = dialog.stage_combo.currentText().strip() if hasattr(dialog, 'stage_combo') else "Planning"
                risk = dialog.risk_combo.currentText().strip() if hasattr(dialog, 'risk_combo') else "Medium"

                ds = DashboardService(session)
                proj = ds.create_audit_project(
                    client_id=client_id, financial_year=fy, status=status, risk_level=risk
                )
                proj_id = proj.id

                self.populate_client_selector()
                idx = self.client_selector.findData(proj_id)
                if idx >= 0: self.client_selector.setCurrentIndex(idx)
                self.data_changed.emit()
                QMessageBox.information(self, "Audit Created", f"Successfully initialized new {audit_type} for FY {fy}.")

    def populate_client_selector(self):
        self.client_selector.clear()
        with get_session() as session:
            ds = DashboardService(session)
            results = ds.get_clients_with_projects()

            client_projects = {}
            for client, proj in results:
                if client.id not in client_projects:
                    client_projects[client.id] = (client, [])
                if proj:
                    client_projects[client.id][1].append(proj)

            if not client_projects:
                # Empty database — add placeholder; do NOT auto-create anything
                self.client_selector.addItem("— No Active Audit —", None)
                return

            for client_id, (c, projs) in client_projects.items():
                if projs:
                    for proj in projs:
                        fy = proj.financial_year or "2025-26"
                        self.client_selector.addItem(f"{c.name} (FY {fy})", proj.id)
                else:
                    self.client_selector.addItem(f"{c.name} (FY 2025-26)", f"client_{c.id}")

    def on_active_engagement_changed(self, index):
        data = self.client_selector.currentData()
        # Guard: None means placeholder (no clients/projects yet)
        if data is None:
            return
        try:
            with get_session() as session:
                ds = DashboardService(session)
                if isinstance(data, str) and data.startswith("client_"):
                    client_id = int(data.split("_")[1])
                    proj = ds.get_or_create_client_project(client_id)
                elif isinstance(data, int):
                    proj = ds.get_audit_project(int(data))
                else:
                    return  # unknown data type — skip safely

                if proj:
                    self.workflow_manager.initialize_engagement(
                        engagement_id=proj.id,
                        client_id=proj.client_id,
                        financial_year=proj.financial_year or "2025-26"
                    )
                    for attr in ['ai_page', 'risk_page', 'reports_page', 'gst_page']:
                        page = getattr(self, attr, None)
                        if page is not None:
                            page.active_engagement_id = proj.id
                            if hasattr(page, 'load_findings'):
                                try: page.load_findings()
                                except Exception: pass
                            if hasattr(page, 'load_database_findings'):
                                try: page.load_database_findings()
                                except Exception: pass
                            if hasattr(page, 'load_active_document_view'):
                                try: page.load_active_document_view()
                                except Exception: pass
        except (SQLAlchemyError, ValueError, RuntimeError) as e:
            logger.warning(f"Engagement change warning: {e}")

    def _setup_nav_shortcuts(self):
        for i in range(min(9, len(self.nav_buttons))):
            btn = self.nav_buttons[i]
            shortcut = QShortcut(QKeySequence(f"Alt+{i+1}"), self)
            shortcut.activated.connect(btn.click)
            btn.setToolTip(f"Hotkey: Alt+{i+1}")
            
        self.f5_shortcut = QShortcut(QKeySequence("F5"), self)
        self.f5_shortcut.activated.connect(self.refresh_realtime_data)
        
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self.settings_shortcut.activated.connect(self.btn_settings.click)

    def setup_keyboard_shortcuts(self):
        """Initializes both global search and navigation keyboard shortcuts."""
        self._setup_search_shortcut()
        self._setup_nav_shortcuts()


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
            "No active alerts or upcoming statutory deadlines for this engagement."
        )

    def closeEvent(self, event):
        event.accept()
