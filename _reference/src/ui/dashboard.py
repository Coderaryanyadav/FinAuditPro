"""
Enterprise Dashboard Module for FinAuditPro.
Redesigned with Model-View Architecture (QAbstractTableModel + QTableView + QStyledItemDelegate),
Real-Time Signal/Slot Automatic Data Refresh, QtCharts QSplineSeries,
Action-Oriented "Needs Attention" Panel, and Trustworthy Slate Enterprise UI Design.
"""

import os
import logging
from datetime import datetime
from typing import List, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout, 
                               QTableView, QHeaderView, QStackedWidget, QLineEdit, 
                               QComboBox, QProgressBar, QMenu, QStyledItemDelegate,
                               QStyleOptionViewItem, QMessageBox, QDialog, QStyle, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QSize, Slot, QAbstractTableModel, QModelIndex, QRect, Signal, QMargins, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QIcon, QBrush, QPen, QKeySequence, QShortcut
from PySide6.QtCharts import QChart, QChartView, QSplineSeries, QCategoryAxis, QValueAxis, QBarCategoryAxis

from database.database import get_session
from database.models import Client, AuditProject, Finding, Engagement, Document, ComplianceTask, ReviewNote
from services.client_service import ClientService
from services.dashboard_service import DashboardService
from security.security_manager import SecurityManager
from security.rbac import Permission
from workflow.workflow_manager import WorkflowManager
from workflow.workflow_events import WorkflowEventManager
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget, get_qss
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
from .findings import FindingsWorkspaceWidget
from .icons import get_app_icon, get_app_pixmap
from .command_palette import CommandPaletteDialog
from .theme import ThemeManager, Colors

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
    
    HEADERS = ["CLIENT NAME", "AUDIT TYPE & FY", "STATUS", "RISK LEVEL", "LAST UPDATED", "ACTION"]
    
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
                    'status': getattr(p, 'status', 'Execution'),
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
                return proj.get('status') or "Execution"
            elif col == 3:
                return proj.get('risk_level') or "Low"
            elif col == 4:
                return proj.get('created_at_str') or "Today"
            elif col == 5:
                return "Open Audit →"

        elif role == Qt.ItemDataRole.UserRole:
            return proj.get('id')

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (2, 3):
                return int(Qt.AlignmentFlag.AlignCenter)
            elif col in (4, 5):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def update_projects(self, new_projects: List[Any]):
        self.beginResetModel()
        self._projects = self._normalize(new_projects)
        self._load_client_cache()
        self.endResetModel()

class AuditStatusDelegate(QStyledItemDelegate):
    """Custom Delegate to draw status pill badges and colored risk dots in QTableView."""
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(120, 44)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        col = index.column()
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        is_dark = ThemeManager().is_dark
        text_color = QColor("#FFFFFF") if is_dark else QColor("#1D1D1F")
        sub_text_color = QColor("#8E8E93") if is_dark else QColor("#6E6E73")
        
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect

        # Alternate row background colors
        if bool(option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(rect, QColor(10, 132, 255, 40) if is_dark else QColor(0, 122, 255, 25))
        elif index.row() % 2 == 1:
            painter.fillRect(rect, QColor("#222224" if is_dark else "#F9F9FB"))
        else:
            painter.fillRect(rect, QColor("#1C1C1E" if is_dark else "#FFFFFF"))

        base_font = QFont(option.font)
        base_font.setPointSize(10)

        if col == 2: # Status Pill
            if "Execution" in text or "Active" in text or "In Progress" in text:
                bg_color = QColor(10, 132, 255, 35) if is_dark else QColor(0, 122, 255, 25)
                pill_fg = QColor("#0A84FF") if is_dark else QColor("#007AFF")
                border_color = QColor(10, 132, 255, 90) if is_dark else QColor(0, 122, 255, 75)
            elif "Completed" in text:
                bg_color = QColor(48, 209, 88, 35) if is_dark else QColor(52, 199, 89, 25)
                pill_fg = QColor("#30D158") if is_dark else QColor("#34C759")
                border_color = QColor(48, 209, 88, 90) if is_dark else QColor(52, 199, 89, 75)
            else:
                bg_color = QColor(255, 159, 10, 35) if is_dark else QColor(255, 159, 10, 25)
                pill_fg = QColor("#FFD60A") if is_dark else QColor("#FF9F0A")
                border_color = QColor(255, 159, 10, 90) if is_dark else QColor(255, 159, 10, 75)
            
            pill_rect = rect.adjusted(8, 7, -8, -7)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1))
            painter.drawRoundedRect(pill_rect, 6, 6)
            
            painter.setPen(QPen(pill_fg))
            base_font.setBold(True)
            painter.setFont(base_font)
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, text)

        elif col == 3: # Risk Level Dot
            dot_color = QColor("#30D158" if is_dark else "#34C759") if "Low" in text else QColor("#FFD60A" if is_dark else "#FF9F0A") if "Medium" in text else QColor("#FF453A" if is_dark else "#FF3B30")
            dot_x = rect.left() + 16
            dot_y = rect.top() + (rect.height() // 2) - 4
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(dot_x, dot_y, 8, 8)
            
            text_rect = rect.adjusted(32, 0, 0, 0)
            painter.setPen(QPen(text_color))
            base_font.setBold(False)
            painter.setFont(base_font)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

        elif col == 5: # Action Button
            btn_rect = rect.adjusted(10, 6, -10, -6)
            btn_bg = QColor(10, 132, 255, 30) if is_dark else QColor(0, 122, 255, 18)
            btn_border = QColor(10, 132, 255, 80) if is_dark else QColor(0, 122, 255, 65)
            btn_fg = QColor("#0A84FF") if is_dark else QColor("#007AFF")
            painter.setBrush(QBrush(btn_bg))
            painter.setPen(QPen(btn_border, 1))
            painter.drawRoundedRect(btn_rect, 6, 6)
            painter.setPen(QPen(btn_fg))
            base_font.setBold(True)
            painter.setFont(base_font)
            painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Open Audit →")

        else: # Regular text columns (Client Name, Audit Type & FY, Last Updated)
            text_rect = rect.adjusted(12, 0, -12, 0)
            painter.setPen(QPen(text_color if col == 0 else sub_text_color))
            base_font.setBold(True if col == 0 else False)
            painter.setFont(base_font)
            align = Qt.AlignmentFlag.AlignRight if col == 4 else Qt.AlignmentFlag.AlignLeft
            painter.drawText(text_rect, align | Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()

class SidebarButton(QPushButton):
    """Modern Enterprise Sidebar Button with active indicator tab & SVG QIcon."""
    def __init__(self, text, icon_name="", is_active=False, parent=None):
        super().__init__(parent)
        self.setObjectName("navButton")
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(f"  {text}")
        if icon_name:
            self.setIcon(get_app_icon(icon_name, color="#38bdf8" if is_active else "#94a3b8", size=18))
            self.setIconSize(QSize(18, 18))
        self.set_active(is_active)

    def set_active(self, is_active: bool):
        self.setProperty("active", "true" if is_active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

class GlobalSearchWidget(QFrame):
    """Global Desktop Search Bar with embedded Ctrl+K keycap badge & search menu."""
    result_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(380, 38)
        self.setObjectName("globalSearchFrame")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        is_dark = ThemeManager().is_dark
        icon_clr = "#8E8E93" if is_dark else "#6E6E73"
        text_clr = "#FFFFFF" if is_dark else "#1D1D1F"
        badge_bg = "#2C2C2E" if is_dark else "#FFFFFF"
        badge_border = "#38383A" if is_dark else "#E5E5EA"

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"font-size: 13px; border: none; background: transparent; color: {icon_clr};")
        search_icon.setObjectName("globalSearchIcon")
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Search clients, findings, reports...")
        self.input_field.setObjectName("globalSearchInput")
        self.input_field.setStyleSheet(f"QLineEdit#globalSearchInput {{ border: none; background: transparent; font-size: 13px; font-weight: 500; color: {text_clr}; placeholder-text-color: {icon_clr}; }}")
        self.input_field.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.input_field.textChanged.connect(self._on_search_text_changed)
        
        shortcut_badge = QLabel("⌘K")
        shortcut_badge.setObjectName("globalShortcutBadge")
        shortcut_badge.setStyleSheet(f"QLabel#globalShortcutBadge {{ border: 1px solid {badge_border}; background-color: {badge_bg}; color: {icon_clr}; font-size: 11px; font-weight: 600; border-radius: 4px; padding: 2px 6px; }}")
        
        layout.addWidget(search_icon)
        layout.addWidget(self.input_field, 1)
        layout.addWidget(shortcut_badge)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.input_field.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        parent_dash = self.window()
        if hasattr(parent_dash, 'open_command_palette'):
            parent_dash.open_command_palette()
        super().mousePressEvent(event)

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
    """Minimal Apple-style Metric Block."""
    def __init__(self, title, value, subtitle, badge_bg, badge_fg, accent_hex="#007AFF", icon_str="", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(100)
        self.setObjectName("metricCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setObjectName("metricValue")
        
        self.badge_lbl = QLabel(subtitle)
        self.badge_lbl.setStyleSheet(f"color: {badge_fg}; font-size: 10px; font-weight: 600; background-color: {badge_bg}; padding: 2px 7px; border-radius: 6px; border: none;")
        
        top_row.addWidget(self.val_lbl)
        top_row.addStretch()
        top_row.addWidget(self.badge_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("metricTitle")
        
        layout.addLayout(top_row)
        layout.addWidget(self.title_lbl)

    def update_value(self, value):
        self.val_lbl.setText(str(value))

class NeedsAttentionPanel(QFrame):
    """Action-oriented 'Needs Attention' Section Panel for Auditors."""
    item_clicked = Signal(int) # target page index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("needsAttentionPanel")
        is_dark = ThemeManager().is_dark
        card_bg = "#222224" if is_dark else "#FFFFFF"
        card_border = "#2E2E32" if is_dark else "#E5E5EA"
        self.setStyleSheet(f"""
            QFrame#needsAttentionPanel {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(8)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("NEEDS ATTENTION")
        title_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #FF9F0A; letter-spacing: 0.5px; border: none; background: transparent; background-color: transparent;")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)

        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(8)
        self.layout.addLayout(self.list_container)

        self.refresh_attention_items()

    def refresh_attention_items(self, engagement_id: int = None):
        while self.list_container.count():
            child = self.list_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = []
        try:
            with get_session() as session:
                q_findings = session.query(Finding).filter_by(is_resolved=False)
                if engagement_id:
                    q_findings = q_findings.filter(Finding.audit_id == engagement_id)
                high_findings = q_findings.filter(Finding.severity == 'High').count()
                if high_findings > 0:
                    items.append({
                        "label": f"{high_findings} High-Risk Anomaly Finding{'s' if high_findings > 1 else ''} require partner review",
                        "badge": "HIGH RISK",
                        "bg": "rgba(255, 59, 48, 0.1)", "fg": "#FF3B30",
                        "target_page": 3
                    })

                q_docs = session.query(Document)
                if engagement_id:
                    q_docs = q_docs.filter(Document.engagement_id == engagement_id)
                unparsed_docs = q_docs.filter(Document.ocr_confidence < 90.0).count()
                if unparsed_docs > 0:
                    items.append({
                        "label": f"{unparsed_docs} Ingested Document{'s' if unparsed_docs > 1 else ''} pending low-confidence OCR verification",
                        "badge": "DOC REVIEW",
                        "bg": "rgba(255, 159, 10, 0.1)", "fg": "#FF9F0A",
                        "target_page": 2
                    })

                q_comp = session.query(ComplianceTask).filter_by(is_completed=False)
                if engagement_id:
                    q_comp = q_comp.filter(ComplianceTask.engagement_id == engagement_id)
                pending_comp = q_comp.count()
                if pending_comp > 0:
                    items.append({
                        "label": f"{pending_comp} Statutory CARO 2020 Compliance Task{'s' if pending_comp > 1 else ''} pending sign-off",
                        "badge": "COMPLIANCE",
                        "bg": "rgba(88, 86, 214, 0.1)", "fg": "#5856D6",
                        "target_page": 6
                    })

                high_risk_projects = session.query(AuditProject).filter(AuditProject.risk_level.in_(["High", "Critical"])).count()
                if high_risk_projects > 0:
                    items.append({
                        "label": f"{high_risk_projects} High Exposure Audit Engagement{'s' if high_risk_projects > 1 else ''} flagged for review",
                        "badge": "HIGH RISK",
                        "bg": "rgba(255, 59, 48, 0.1)", "fg": "#FF3B30",
                        "target_page": 5
                    })

        except Exception as e:
            logger.warning(f"Could not load needs attention items: {e}")

        if not items:
            empty_box = QFrame()
            empty_box.setObjectName("attentionRow")
            empty_box.setStyleSheet("""
                QFrame#attentionRow {
                    background-color: rgba(52, 199, 89, 0.06);
                    border: 1px solid rgba(52, 199, 89, 0.2);
                    border-radius: 8px;
                }
            """)
            ebl = QHBoxLayout(empty_box)
            ebl.setContentsMargins(12, 10, 12, 10)
            ebl.setSpacing(10)
            
            chk = QLabel("✓")
            chk.setStyleSheet("font-size: 14px; font-weight: 700; color: #34C759; border: none; background: transparent;")
            
            msg = QLabel("All caught up — no high-priority items require immediate action.")
            msg.setStyleSheet("font-size: 12px; font-weight: 600; color: #34C759; border: none; background: transparent;")
            msg.setWordWrap(True)
            
            ebl.addWidget(chk)
            ebl.addWidget(msg, 1)
            self.list_container.addWidget(empty_box)
        else:
            for item in items[:3]:
                row = QFrame()
                row.setObjectName("attentionRow")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(10, 7, 10, 7)
                rl.setSpacing(10)

                badge = QLabel(item["badge"])
                badge.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {item['fg']}; background: {item['bg']}; padding: 2px 7px; border-radius: 4px; border: none;")

                txt = QLabel(item["label"])
                txt.setObjectName("attentionLabel")
                txt.setWordWrap(True)

                btn = QPushButton("Review →")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("font-size: 11px; font-weight: 600; color: #007AFF; background: transparent; background-color: transparent; border: none;")
                target_idx = item["target_page"]
                btn.clicked.connect(lambda checked=False, p=target_idx: self.item_clicked.emit(p))

                rl.addWidget(badge)
                rl.addWidget(txt, 1)
                rl.addWidget(btn)
                self.list_container.addWidget(row)

class RiskMatrixWidget(QFrame):
    """Minimal Apple-style Risk Summary Block."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("riskMatrixWidget")
        is_dark = ThemeManager().is_dark
        card_bg = "#222224" if is_dark else "#FFFFFF"
        card_border = "#2E2E32" if is_dark else "#E5E5EA"
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        self.setStyleSheet(f"""
            QFrame#riskMatrixWidget {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title_lbl = QLabel("RISK SUMMARY")
        title_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #86868B; letter-spacing: 0.5px; border: none; background: transparent; background-color: transparent;")
        layout.addWidget(title_lbl)

        v_box = QVBoxLayout()
        v_box.setSpacing(8)

        self.row_crit = self._create_risk_row("Critical Anomaly Findings", "0", "#FF453A" if is_dark else "#FF3B30")
        self.row_high = self._create_risk_row("High Exposure Findings", "0", "#FFD60A" if is_dark else "#FF9F0A")
        self.row_med  = self._create_risk_row("Medium Category Anomalies", "0", "#5E5CE6" if is_dark else "#5856D6")
        self.row_low  = self._create_risk_row("Low Risk Observations", "0", "#30D158" if is_dark else "#34C759")

        v_box.addLayout(self.row_crit)
        v_box.addLayout(self.row_high)
        v_box.addLayout(self.row_med)
        v_box.addLayout(self.row_low)
        layout.addLayout(v_box)

    def _create_risk_row(self, label: str, val: str, color_hex: str) -> QHBoxLayout:
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        is_dark = ThemeManager().is_dark
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color_hex}; font-size: 10px; border: none; background: transparent; background-color: transparent;")

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {text_clr}; border: none; background: transparent; background-color: transparent;")

        v_lbl = QLabel(val)
        v_lbl.setObjectName("valLabel")
        v_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {text_clr}; border: none; background: transparent; background-color: transparent;")

        hl.addWidget(dot)
        hl.addSpacing(6)
        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(v_lbl)
        return hl

    def update_counts(self, crit: int, high: int, med: int, low: int):
        for hl, val in [(self.row_crit, crit), (self.row_high, high), (self.row_med, med), (self.row_low, low)]:
            item = hl.itemAt(3)
            if item and item.widget():
                item.widget().setText(str(val))

class AuditWorkspacePanel(QFrame):
    """
    16-Stage Enterprise Audit Workspace Control Panel for FinAuditPro.
    Displays current engagement context, 16-stage audit lifecycle progress stepper,
    and dynamic next-step CTA button connected to WorkflowManager.
    """
    def __init__(self, parent_dashboard=None):
        super().__init__()
        self.parent_dashboard = parent_dashboard
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("auditWorkspacePanel")
        is_dark = ThemeManager().is_dark
        card_bg = "#222224" if is_dark else "#FFFFFF"
        card_border = "#2E2E32" if is_dark else "#E5E5EA"
        self.setStyleSheet(f"""
            QFrame#auditWorkspacePanel {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        row1_h = QHBoxLayout()
        row1_h.setSpacing(12)

        self.lbl_title = QLabel("ACTIVE AUDIT WORKSPACE")
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #86868B; letter-spacing: 0.5px; border: none; background: transparent; background-color: transparent;")

        self.lbl_pct = QLabel("0% Complete")
        self.lbl_pct.setStyleSheet("font-size: 11px; font-weight: 600; color: #007AFF; background: rgba(0, 122, 255, 0.1); padding: 3px 8px; border-radius: 6px;")

        row1_h.addWidget(self.lbl_title)
        row1_h.addStretch()
        row1_h.addWidget(self.lbl_pct)
        layout.addLayout(row1_h)

        is_dark = ThemeManager().is_dark
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        ab_bg = "#2A2A2D" if is_dark else "#F2F2F7"
        ab_border = "#3A3A3E" if is_dark else "#E5E5EA"

        self.lbl_engagement_info = QLabel("No Active Engagement Selected")
        self.lbl_engagement_info.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {text_clr}; border: none; background: transparent; background-color: transparent;")
        layout.addWidget(self.lbl_engagement_info)

        # 16-Stage Stepper Bar
        self.stepper_scroll = QScrollArea()
        self.stepper_scroll.setWidgetResizable(True)
        self.stepper_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.stepper_scroll.setFixedHeight(46)
        self.stepper_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.stepper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stepper_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:horizontal { height: 4px; background: transparent; margin: 0px; }
            QScrollBar::handle:horizontal { background: #3A3A3C; border-radius: 2px; min-width: 30px; }
            QScrollBar::handle:horizontal:hover { background: #636366; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; background: none; }
        """)

        self.stepper_widget = QWidget()
        self.stepper_widget.setStyleSheet("background: transparent;")
        self.stepper_h = QHBoxLayout(self.stepper_widget)
        self.stepper_h.setContentsMargins(0, 0, 0, 0)
        self.stepper_h.setSpacing(8)
        self.stepper_scroll.setWidget(self.stepper_widget)

        layout.addWidget(self.stepper_scroll)

        action_bar = QFrame()
        action_bar.setObjectName("workspaceActionBar")
        action_bar.setStyleSheet(f"QFrame#workspaceActionBar {{ background-color: {ab_bg}; border: 1px solid {ab_border}; border-radius: 8px; }}")
        ab_layout = QHBoxLayout(action_bar)
        ab_layout.setContentsMargins(12, 7, 12, 7)

        self.lbl_next_action = QLabel("Recommended: Create or select an audit engagement to begin.")
        self.lbl_next_action.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {text_clr}; border: none; background: transparent; background-color: transparent;")

        self.btn_next_action = QPushButton("Next Step →")
        self.btn_next_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next_action.setObjectName("primaryBtn")
        self.btn_next_action.setStyleSheet("""
            QPushButton#primaryBtn {
                background-color: #007AFF;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 12px;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton#primaryBtn:hover {
                background-color: #0062CC;
            }
        """)
        self.btn_next_action.clicked.connect(self._on_action_clicked)

        ab_layout.addWidget(self.lbl_next_action)
        ab_layout.addStretch()
        ab_layout.addWidget(self.btn_next_action)
        layout.addWidget(action_bar)

        self._target_page_idx = 1
        self.refresh_workspace_state()

    def refresh_workspace_state(self):
        try:
            from workflow.workflow_manager import WorkflowManager
            from workflow.workflow_state import AuditStage
            wm = WorkflowManager()
            summary = wm.get_dashboard_summary()

            while self.stepper_h.count():
                child = self.stepper_h.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            all_stages = AuditStage.stage_order()
            curr_stage_name = summary.get("current_stage", "ENGAGEMENT_CREATED")
            curr_stage_obj = AuditStage.CLIENT_CREATED
            for s in all_stages:
                if s.value == curr_stage_name or s.name == curr_stage_name:
                    curr_stage_obj = s
                    break

            curr_idx = curr_stage_obj.get_index()
            active_pill_widget = None

            for idx, stage in enumerate(all_stages):
                stage_display = stage.value.replace('_', ' ').title()
                label_text = f"{idx+1}. {stage_display}"
                if idx < curr_idx:
                    label_text = f"✓ {label_text}"

                pill = QLabel(label_text)
                pill.setFixedHeight(28)
                pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pill.setWordWrap(False)

                fm = pill.fontMetrics()
                req_w = fm.horizontalAdvance(label_text) + 24
                pill.setMinimumWidth(max(110, req_w))
                pill.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

                if idx < curr_idx:
                    pill.setStyleSheet("background-color: rgba(52, 199, 89, 0.12); color: #34C759; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(52, 199, 89, 0.3);")
                elif idx == curr_idx:
                    pill.setStyleSheet("background-color: #007AFF; color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 6px; border: none;")
                    active_pill_widget = pill
                else:
                    pill.setStyleSheet("background-color: #F2F2F7; color: #86868B; font-size: 11px; font-weight: 500; padding: 3px 10px; border-radius: 6px; border: 1px solid #E5E5EA;")
                self.stepper_h.addWidget(pill)

            self.stepper_h.addStretch()

            if active_pill_widget:
                QTimer.singleShot(100, lambda w=active_pill_widget: self.stepper_scroll.ensureWidgetVisible(w))

            pct = summary.get("completion_percentage", 0.0)
            self.lbl_pct.setText(f"{pct:.0f}% Complete")

            client_name = ""
            if self.parent_dashboard and hasattr(self.parent_dashboard, 'client_selector') and self.parent_dashboard.client_selector.count() > 0:
                cur_txt = self.parent_dashboard.client_selector.currentText().strip()
                if cur_txt and not cur_txt.startswith("—"):
                    client_name = cur_txt

            if client_name:
                self.lbl_engagement_info.setText(f"Audit Target: {client_name} • Stage: {curr_stage_obj.value.replace('_', ' ').title()}")
            elif summary.get("active_engagement"):
                self.lbl_engagement_info.setText(f"Audit Target: Engagement #{summary.get('active_engagement')} • Stage: {curr_stage_obj.value.replace('_', ' ').title()}")
            else:
                self.lbl_engagement_info.setText("No Active Audit Project Selected — Choose from Header Selector")

            # Update CTA & Target Page Mapping
            if curr_idx < 3:
                self.lbl_next_action.setText("🎯 Recommended Next Step: Initialize client engagement & statutory parameters")
                self.btn_next_action.setText("Go to Client Management →")
                self._target_page_idx = 1
            elif curr_idx == 3:
                self.lbl_next_action.setText("🎯 Recommended Next Step: Calculate SA 320 Materiality benchmarks (Overall & Performance)")
                self.btn_next_action.setText("Run Materiality Calculator →")
                self._target_page_idx = 7
            elif curr_idx in (4, 5, 6):
                self.lbl_next_action.setText("🎯 Recommended Next Step: Ingest Client Trial Balance & Bank Statements")
                self.btn_next_action.setText("Upload Audit Documents →")
                self._target_page_idx = 2
            elif curr_idx == 7:
                self.lbl_next_action.setText("🎯 Recommended Next Step: Execute local RAG AI Audit Copilot to detect statutory anomalies")
                self.btn_next_action.setText("Run AI Audit Analysis →")
                self._target_page_idx = 3
            elif curr_idx == 8:
                self.lbl_next_action.setText("🎯 Recommended Next Step: Assess identified SA 315 audit risks & financial exposure")
                self.btn_next_action.setText("View Risk Matrix →")
                self._target_page_idx = 7
            elif curr_idx in (9, 10, 11):
                self.lbl_next_action.setText("🎯 Recommended Next Step: Review electronic SA 230 Working Papers & link evidence")
                self.btn_next_action.setText("Open Working Papers →")
                self._target_page_idx = 8
            elif curr_idx == 12:
                self.lbl_next_action.setText("🎯 Recommended Next Step: Perform CARO 2020 & Form 3CD statutory compliance review")
                self.btn_next_action.setText("Review Compliance Matrix →")
                self._target_page_idx = 6
            else:
                self.lbl_next_action.setText("🎯 Recommended Next Step: Finalize Partner 3-Tier sign-off & generate SA 700/705 Audit Report")
                self.btn_next_action.setText("Generate Audit Report →")
                self._target_page_idx = 9

        except Exception as e:
            logger.warning(f"Failed to refresh AuditWorkspacePanel state: {e}")

    def _on_action_clicked(self):
        if self.parent_dashboard and hasattr(self.parent_dashboard, 'nav_buttons'):
            if 0 <= self._target_page_idx < len(self.parent_dashboard.nav_buttons):
                self.parent_dashboard.nav_buttons[self._target_page_idx].click()

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
        
        sidebar = self._build_sidebar()
        
        main_content = QFrame()
        main_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        main_content.setObjectName("appBg")
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
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("dashboardSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        logo_container = QFrame()
        logo_container.setFixedHeight(64)
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
        nav_layout.setContentsMargins(10, 12, 10, 12)
        nav_layout.setSpacing(2)

        def add_section(title: str):
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #86868B; padding: 10px 8px 4px 8px; letter-spacing: 0.5px; border: none; background: transparent; background-color: transparent;")
            nav_layout.addWidget(lbl)

        def add_separator():
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet("background-color: #E5E5EA; margin: 6px 8px;")
            nav_layout.addWidget(sep)

        add_section("WORKSPACE")
        self.btn_dashboard = SidebarButton("Dashboard", "dashboard", True)
        self.btn_clients = SidebarButton("Clients", "clients")
        self.btn_upload = SidebarButton("Documents", "documents")
        nav_layout.addWidget(self.btn_dashboard)
        nav_layout.addWidget(self.btn_clients)
        nav_layout.addWidget(self.btn_upload)

        add_separator()
        add_section("FINANCIAL")
        self.btn_statements = SidebarButton("Financial Statements", "statements")
        self.btn_gst = SidebarButton("GST Verification", "check")
        self.btn_compliance = SidebarButton("Compliance", "compliance")
        nav_layout.addWidget(self.btn_statements)
        nav_layout.addWidget(self.btn_gst)
        nav_layout.addWidget(self.btn_compliance)

        add_separator()
        add_section("ANALYSIS")
        self.btn_risk = SidebarButton("Risk Analysis", "risk")
        self.btn_ai = SidebarButton("AI Audit Analysis", "ai")
        self.btn_findings = SidebarButton("Audit Findings", "alert")
        nav_layout.addWidget(self.btn_risk)
        nav_layout.addWidget(self.btn_ai)
        nav_layout.addWidget(self.btn_findings)

        add_separator()
        add_section("AUDIT WORKFLOW")
        self.btn_working_papers = SidebarButton("Working Papers", "papers")
        self.btn_reports = SidebarButton("Audit Reports", "reports")
        self.btn_history = SidebarButton("Audit History", "history")
        nav_layout.addWidget(self.btn_working_papers)
        nav_layout.addWidget(self.btn_reports)
        nav_layout.addWidget(self.btn_history)

        add_separator()
        add_section("SYSTEM")
        self.btn_settings = SidebarButton("Settings", "settings")
        nav_layout.addWidget(self.btn_settings)
        
        self.nav_buttons = [
            self.btn_dashboard, self.btn_clients, self.btn_upload,
            self.btn_statements, self.btn_gst, self.btn_compliance,
            self.btn_risk, self.btn_ai, self.btn_findings,
            self.btn_working_papers, self.btn_reports, self.btn_history,
            self.btn_settings
        ]
        
        nav_layout.addStretch()
        nav_scroll.setWidget(nav_widget)
        sidebar_layout.addWidget(nav_scroll)
        
        profile_frame = QFrame()
        profile_frame.setFixedHeight(64)
        profile_frame.setObjectName("sidebarProfileFrame")
        profile_layout = QHBoxLayout(profile_frame)
        profile_layout.setContentsMargins(16, 0, 16, 0)
        
        try:
            display_name = self.current_user.username if self.current_user else "admin"
            display_role = self.current_user.role if self.current_user else "Audit Partner"
        except Exception:
            display_name = "admin"
            display_role = "Audit Partner"
        avatar_text = display_name[:2].upper() if display_name else "AD"

        avatar_lbl = QLabel(avatar_text)
        avatar_lbl.setFixedSize(32, 32)
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
        header_layout.setSpacing(12)

        is_dark = ThemeManager().is_dark
        combo_bg = "#1E1E1E" if is_dark else "#F2F2F7"
        combo_border = "#38383A" if is_dark else "#E5E5EA"
        combo_text = "#FFFFFF" if is_dark else "#1D1D1F"

        tool_bg = "#2C2C2E" if is_dark else "#F2F2F7"
        tool_border = "#38383A" if is_dark else "#E5E5EA"
        tool_text = "#FFFFFF" if is_dark else "#1D1D1F"

        # 1. Global Search Bar (380x38px)
        self.search_bar = GlobalSearchWidget()
        self.search_bar.result_selected.connect(self._on_search_result_selected)
        header_layout.addWidget(self.search_bar)

        header_layout.addStretch()

        # 2. Active Audit Context Box
        lbl_act = QLabel("ACTIVE AUDIT")
        lbl_act.setStyleSheet("font-size: 10px; font-weight: 700; color: #86868B; letter-spacing: 0.5px; text-transform: uppercase; border: none; background: transparent; background-color: transparent;")

        self.client_selector = QComboBox()
        self.client_selector.setMinimumWidth(260)
        self.client_selector.setMaximumWidth(340)
        self.client_selector.setFixedHeight(36)
        self.client_selector.setObjectName("clientSelectorCombo")
        self.populate_client_selector()
        self.client_selector.currentIndexChanged.connect(self.on_active_engagement_changed)

        self.header_status_badge = QLabel("In Progress")
        self.header_status_badge.setObjectName("statusBadgeBlue")

        header_layout.addWidget(lbl_act)
        header_layout.addWidget(self.client_selector)
        header_layout.addWidget(self.header_status_badge)
        header_layout.addSpacing(8)

        # 3. Clean Vertical Divider
        div = QFrame()
        div.setFixedSize(1, 28)
        div.setObjectName("headerDivider")
        div.setStyleSheet("background-color: rgba(142, 142, 147, 0.3);")
        header_layout.addWidget(div)
        header_layout.addSpacing(8)

        # 4. Primary CTA + New Audit
        btn_new_audit = QPushButton("+ New Audit")
        btn_new_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_audit.setFixedHeight(38)
        btn_new_audit.setObjectName("primaryBtn")
        btn_new_audit.clicked.connect(self.open_create_audit_dialog)
        header_layout.addWidget(btn_new_audit)

        # 5. Dedicated 36x36px Utility Tool Buttons (Theme, Help, Notifications)
        self.btn_theme_toggle = QPushButton("🌙" if not is_dark else "☀️")
        self.btn_theme_toggle.setFixedSize(36, 36)
        self.btn_theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_toggle.setObjectName("iconToolBtn")
        self.btn_theme_toggle.setToolTip("Toggle Dark/Light Theme (⌘K -> Toggle Theme)")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme_mode)

        self.btn_help = QPushButton("?")
        self.btn_help.setFixedSize(36, 36)
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setObjectName("iconToolBtn")
        self.btn_help.setToolTip("Keyboard Shortcuts Reference (⌘K -> Shortcuts)")
        self.btn_help.clicked.connect(self.show_keyboard_shortcuts_dialog)

        self.btn_notif = QPushButton("🔔")
        self.btn_notif.setFixedSize(36, 36)
        self.btn_notif.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_notif.setObjectName("iconToolBtn")
        self.btn_notif.setToolTip("Active Audit Alerts")
        self.btn_notif.clicked.connect(self.show_notifications_popup)

        header_layout.addWidget(self.btn_theme_toggle)
        header_layout.addWidget(self.btn_help)
        header_layout.addWidget(self.btn_notif)
        return header

    def _build_overview_page(self) -> QWidget:
        is_dark = ThemeManager().is_dark
        bg_clr = "#18181A" if is_dark else "#F5F5F7"

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("dashboardMainScroll")
        scroll.setStyleSheet(f"QScrollArea#dashboardMainScroll {{ background-color: {bg_clr}; border: none; }} QScrollArea#dashboardMainScroll > QWidget {{ background-color: {bg_clr}; }}")

        body_widget = QFrame()
        body_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body_widget.setObjectName("dashboardMainBody")
        body_widget.setStyleSheet(f"QFrame#dashboardMainBody {{ background-color: {bg_clr}; border: none; }}")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(28, 24, 28, 28)
        body_layout.setSpacing(20)
        
        # 1. Native Apple-Style Page Header
        self.audit_overview_header = QFrame()
        self.audit_overview_header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.audit_overview_header.setStyleSheet("background: transparent; border: none;")
        aoh_layout = QHBoxLayout(self.audit_overview_header)
        aoh_layout.setContentsMargins(0, 0, 0, 0)

        aoh_left = QVBoxLayout()
        aoh_left.setSpacing(4)

        is_dark = ThemeManager().is_dark
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        sub_clr = "#8E8E93" if is_dark else "#86868B"

        self.lbl_overview_title = QLabel("Audit Overview")
        self.lbl_overview_title.setObjectName("heroTitle")
        self.lbl_overview_sub = QLabel("Monitor active engagements, statutory compliance, audit findings, and risk exposure.")
        self.lbl_overview_sub.setObjectName("heroSub")

        aoh_left.addWidget(self.lbl_overview_title)
        aoh_left.addWidget(self.lbl_overview_sub)

        date_lbl = QLabel(datetime.now().strftime("%a, %d %b %Y"))
        date_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #007AFF; background: rgba(0, 122, 255, 0.1); padding: 5px 12px; border-radius: 6px;")

        aoh_layout.addLayout(aoh_left)
        aoh_layout.addStretch()
        aoh_layout.addWidget(date_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        body_layout.addWidget(self.audit_overview_header)

        # 2. Row 1: Active Audit Workspace Panel (60%) + Needs Attention Panel (40%)
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(16)

        self.workspace_panel = AuditWorkspacePanel(parent_dashboard=self)
        self.needs_attention_panel = NeedsAttentionPanel(parent=self)
        self.needs_attention_panel.item_clicked.connect(self._on_search_result_selected)

        row1_layout.addWidget(self.workspace_panel, 6)
        row1_layout.addWidget(self.needs_attention_panel, 4)
        body_layout.addLayout(row1_layout)
        
        # 3. Row 2: 4 Key Metric Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)
        
        self.card_clients = MetricCard("TOTAL CLIENTS", "0", "Registered", "rgba(2, 132, 199, 0.1)", "#0284c7", "#0284c7", "clients")
        self.card_completed = MetricCard("COMPLETED AUDITS", "0", "This Year", "rgba(16, 185, 129, 0.1)", "#047857", "#047857", "check")
        self.card_pending = MetricCard("OPEN FINDINGS", "0", "Action Req.", "rgba(217, 119, 6, 0.1)", "#d97706", "#d97706", "risk")
        self.card_high_risk = MetricCard("HIGH RISK CASES", "0", "Flagged by AI", "rgba(220, 38, 38, 0.1)", "#dc2626", "#dc2626", "shield")

        stats_layout.addWidget(self.card_clients)
        stats_layout.addWidget(self.card_completed)
        stats_layout.addWidget(self.card_pending)
        stats_layout.addWidget(self.card_high_risk)
        body_layout.addLayout(stats_layout)

        # Welcome banner (shown only if 0 clients exist)
        self.welcome_banner = QFrame()
        self.welcome_banner.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.welcome_banner.setObjectName("welcomeBanner")
        self.welcome_banner.setStyleSheet("QFrame#welcomeBanner { background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; }")
        wb_layout = QHBoxLayout(self.welcome_banner)
        wb_layout.setContentsMargins(18, 14, 18, 14)
        wb_layout.setSpacing(14)

        wb_text_v = QVBoxLayout()
        wb_text_v.setSpacing(3)
        wb_title = QLabel("Welcome to FinAuditPro")
        wb_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1D4ED8; border: none; background: transparent; background-color: transparent;")
        wb_sub = QLabel("No clients or audit engagements yet. Start by adding your first client.")
        wb_sub.setStyleSheet("font-size: 12px; color: #3B82F6; border: none; background: transparent; background-color: transparent;")
        wb_text_v.addWidget(wb_title)
        wb_text_v.addWidget(wb_sub)

        btn_add_client = QPushButton("+ Add First Client")
        btn_add_client.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_client.setObjectName("primaryBtn")
        btn_add_client.clicked.connect(lambda: self.btn_clients.click())

        wb_layout.addLayout(wb_text_v, 1)
        wb_layout.addWidget(btn_add_client)
        self.welcome_banner.hide()
        body_layout.addWidget(self.welcome_banner)
        
        # 4. Row 3: Progress Chart (60%) + Risk Matrix (40%)
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(16)
        
        self.progress_chart = AuditProgressChart([])
        self.risk_matrix = RiskMatrixWidget()
        
        row3_layout.addWidget(self.progress_chart, 6)
        row3_layout.addWidget(self.risk_matrix, 4)
        body_layout.addLayout(row3_layout)

        # 5. Row 4: Recent Projects Table Section
        self.recent_projects_frame = QFrame()
        self.recent_projects_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.recent_projects_frame.setObjectName("recentProjectsTableFrame")
        is_dark = ThemeManager().is_dark
        card_bg = "#222224" if is_dark else "#FFFFFF"
        card_border = "#2E2E32" if is_dark else "#E5E5EA"
        tbl_bg = "#1C1C1E" if is_dark else "#FFFFFF"
        tbl_grid = "#2E2E32" if is_dark else "#F2F2F7"
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        hdr_bg = "#2A2A2D" if is_dark else "#F2F2F7"
        hdr_fg = "#8E8E93" if is_dark else "#86868B"
        hdr_border = "#3A3A3E" if is_dark else "#E5E5EA"
        self.recent_projects_frame.setStyleSheet(f"""
            QFrame#recentProjectsTableFrame {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
        """)
        t_layout = QVBoxLayout(self.recent_projects_frame)
        t_layout.setContentsMargins(18, 14, 18, 14)
        t_layout.setSpacing(10)

        t_header = QHBoxLayout()
        t_title = QLabel("Recent Audit Projects")
        t_title.setStyleSheet(f"font-weight: 700; font-size: 15px; color: {text_clr}; border: none; background: transparent; background-color: transparent;")
        t_header.addWidget(t_title)
        t_header.addStretch()
        t_layout.addLayout(t_header)

        self.table_model = AuditProjectsTableModel([])

        self.table_view = QTableView()
        self.table_view.setObjectName("recentProjectsTableView")
        self.table_view.setModel(self.table_model)
        self.table_view.setItemDelegate(AuditStatusDelegate(self.table_view))
        
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.verticalHeader().setDefaultSectionSize(44)
        self.table_view.setShowGrid(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        h_header = self.table_view.horizontalHeader()
        h_header.setFixedHeight(38)
        h_header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        h_header.setMinimumSectionSize(110)
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        h_header.resizeSection(1, 160)
        h_header.resizeSection(2, 130)
        h_header.resizeSection(3, 120)
        h_header.resizeSection(4, 160)
        h_header.resizeSection(5, 130)

        self.table_view.setStyleSheet(f"""
            QTableView#recentProjectsTableView {{
                background-color: {tbl_bg};
                gridline-color: {tbl_grid};
                border: none;
                color: {text_clr};
                font-size: 13px;
                outline: none;
            }}
            QHeaderView::section {{
                background-color: {hdr_bg};
                color: {hdr_fg};
                border: none;
                border-bottom: 1px solid {hdr_border};
                font-weight: 600;
                font-size: 11px;
                padding: 8px 12px;
                letter-spacing: 0.4px;
            }}
        """)
        self.table_view.doubleClicked.connect(self.on_table_double_clicked)

        self.table_empty_widget = EmptyStateWidget(
            title="No Recent Audit Projects",
            description="Create an audit engagement from Client Management or top header selector to start tracking audit projects."
        )

        t_layout.addWidget(self.table_view)
        t_layout.addWidget(self.table_empty_widget)
        
        body_layout.addWidget(self.recent_projects_frame)
        body_layout.addStretch(1)
        scroll.setWidget(body_widget)
        return scroll

    def _build_stacked_pages(self, overview_widget: QWidget) -> QStackedWidget:
        self._page_classes = {
            1: (ClientManagementWidget, "Client Management"),
            2: (DocumentUploadWidget, "Document Upload"),
            3: (AIAuditWidget, "AI Audit Analysis"),
            4: (FindingsWorkspaceWidget, "Audit Findings"),
            5: (FinancialStatementsWidget, "Financial Statements"),
            6: (GSTVerificationWidget, "GST Verification"),
            7: (ComplianceWidget, "Compliance Monitoring"),
            8: (RiskAnalysisWidget, "Risk Analysis"),
            9: (WorkingPaperWidget, "Working Papers"),
            10: (ReportsWidget, "Report Generator"),
            11: (AuditHistoryWidget, "Audit History"),
            12: (SettingsWidget, "System Settings"),
        }
        self._loaded_pages = {0: True}
        stacked_widget = QStackedWidget()
        stacked_widget.addWidget(overview_widget)

        for i in range(1, 13):
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
                1: 'clients_page', 2: 'docs_page', 3: 'ai_page', 4: 'findings_page',
                5: 'statements_page', 6: 'gst_page', 7: 'compliance_page', 8: 'risk_page',
                9: 'working_papers_page', 10: 'reports_page', 11: 'history_page', 12: 'settings_page'
            }
            if index in attr_map:
                setattr(self, attr_map[index], widget)

            # Propagate current active engagement & project IDs to newly loaded page
            if getattr(self, 'current_active_engagement_id', None):
                widget.active_engagement_id = self.current_active_engagement_id
            if getattr(self, 'current_active_project_id', None):
                widget.active_project_id = self.current_active_project_id

            if hasattr(widget, 'load_findings'):
                try: widget.load_findings()
                except Exception: pass
            if hasattr(widget, 'load_database_findings'):
                try: widget.load_database_findings()
                except Exception: pass
            if hasattr(widget, 'load_active_document_view'):
                try: widget.load_active_document_view()
                except Exception: pass
            if hasattr(widget, 'refresh_data'):
                try: widget.refresh_data()
                except Exception: pass
            if hasattr(widget, 'load_tasks'):
                try: widget.load_tasks()
                except Exception: pass
            if hasattr(widget, 'load_working_papers'):
                try: widget.load_working_papers()
                except Exception: pass

    def _setup_search_shortcut(self):
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self.open_command_palette)
        
        self.cmd_k_shortcut = QShortcut(QKeySequence("Cmd+K"), self)
        self.cmd_k_shortcut.activated.connect(self.open_command_palette)

    def open_command_palette(self):
        palette = CommandPaletteDialog(parent=self)
        palette.action_triggered.connect(self.handle_command_palette_action)
        palette.exec()

    def handle_command_palette_action(self, key: str, payload: Any):
        if key == "nav":
            idx = int(payload)
            if 0 <= idx < len(self.nav_buttons):
                self.nav_buttons[idx].click()
        elif key == "action":
            if payload == "new_audit":
                self.open_create_audit_dialog()
            elif payload == "toggle_theme":
                self.toggle_theme_mode()
            elif payload == "refresh":
                self.refresh_realtime_data()
            elif payload == "export_db":
                self._ensure_page_loaded(11)
                if hasattr(self, 'settings_page'):
                    self.settings_page.backup_database()
            elif payload == "test_ollama":
                self._ensure_page_loaded(11)
                if hasattr(self, 'settings_page'):
                    self.settings_page.test_ollama()

    def toggle_theme_mode(self):
        ThemeManager().toggle()
        is_dark = ThemeManager().is_dark
        if hasattr(self, 'btn_theme_toggle'):
            self.btn_theme_toggle.setText("☀️" if is_dark else "🌙")
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_qss(dark=is_dark))

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
        self._ensure_page_loaded(8) # Working Papers index is 8
        self.stacked_widget.setCurrentIndex(8)
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

                # Handle Table vs Empty State visibility & height
                proj_count = len(metrics["recent_projects"])
                if hasattr(self, 'table_empty_widget') and hasattr(self, 'table_view'):
                    if proj_count == 0:
                        self.table_view.hide()
                        self.table_empty_widget.show()
                        self.table_empty_widget.setFixedHeight(120)
                        if hasattr(self, 'recent_projects_frame'):
                            self.recent_projects_frame.setFixedHeight(175)
                    else:
                        if hasattr(self, 'recent_projects_frame'):
                            self.recent_projects_frame.setMinimumHeight(0)
                            self.recent_projects_frame.setMaximumHeight(16777215)
                        self.table_empty_widget.hide()
                        self.table_view.show()
                        calc_h = 38 + (proj_count * 44) + 8
                        self.table_view.setFixedHeight(min(400, max(120, calc_h)))

                # Update Audit Progress Chart
                if hasattr(self, 'progress_chart'):
                    self.progress_chart.update_data(metrics["recent_projects"])

                # Update Risk Matrix Breakdown
                if hasattr(self, 'risk_matrix'):
                    crit = session.query(Finding).filter_by(severity='Critical', is_resolved=False).count()
                    high = session.query(Finding).filter_by(severity='High', is_resolved=False).count()
                    med  = session.query(Finding).filter_by(severity='Medium', is_resolved=False).count()
                    low  = session.query(Finding).filter_by(severity='Low', is_resolved=False).count()
                    self.risk_matrix.update_counts(crit, high, med, low)

                # Refresh Needs Attention Panel
                if hasattr(self, 'needs_attention_panel'):
                    active_id = getattr(self, 'current_active_engagement_id', None)
                    self.needs_attention_panel.refresh_attention_items(active_id)

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

        dialog = CreateAuditProjectDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_id = dialog.client_combo.currentData()
            fy = dialog.fy_combo.currentText().strip()
            audit_type = dialog.audit_type_combo.currentText().strip()
            status = dialog.stage_combo.currentText().strip()
            risk = dialog.risk_combo.currentText().strip()

            from database.database import get_session
            with get_session() as session:
                ds = DashboardService(session)
                proj = ds.create_audit_project(
                    client_id=client_id, financial_year=fy, status=status, risk_level=risk
                )
                proj_id = proj.id

            self.populate_client_selector()
            idx = self.client_selector.findData(proj_id)
            if idx >= 0:
                self.client_selector.setCurrentIndex(idx)
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
        if data is None:
            if hasattr(self, 'lbl_overview_sub'):
                self.lbl_overview_sub.setText("No Active Audit Project Selected")
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
                    return

                if proj:
                    from database.repositories.engagement_repo import EngagementRepository
                    from services.engagement_service import EngagementService
                    eng_svc = EngagementService(EngagementRepository(session))
                    eng = eng_svc.ensure_engagement_for_project(proj.id)
                    target_id = eng.id if eng else proj.id

                    self.current_active_engagement_id = target_id
                    self.current_active_project_id = proj.id

                    client_obj = session.query(Client).filter_by(id=proj.client_id).first()
                    client_name = client_obj.name if client_obj else f"Client #{proj.client_id}"
                    fy_str = proj.financial_year or "2025-26"
                    status_str = proj.status or "In Progress"

                    if hasattr(self, 'lbl_overview_sub'):
                        self.lbl_overview_sub.setText(f"{client_name} · Statutory Audit (FY {fy_str})")
                    if hasattr(self, 'header_status_badge'):
                        self.header_status_badge.setText(status_str)

                    self.workflow_manager.initialize_engagement(
                        engagement_id=target_id,
                        client_id=proj.client_id,
                        financial_year=fy_str
                    )
                    for attr in ['ai_page', 'risk_page', 'reports_page', 'gst_page', 'statements_page', 'compliance_page', 'working_papers_page', 'history_page', 'docs_page']:
                        page = getattr(self, attr, None)
                        if page is not None:
                            page.active_engagement_id = target_id
                            page.active_project_id = proj.id
                            if hasattr(page, 'load_findings'):
                                try: page.load_findings()
                                except Exception: pass
                            if hasattr(page, 'load_database_findings'):
                                try: page.load_database_findings()
                                except Exception: pass
                            if hasattr(page, 'load_active_document_view'):
                                try: page.load_active_document_view()
                                except Exception: pass
                            if hasattr(page, 'refresh_data'):
                                try: page.refresh_data()
                                except Exception: pass
                            if hasattr(page, 'load_tasks'):
                                try: page.load_tasks()
                                except Exception: pass
                            if hasattr(page, 'load_working_papers'):
                                try: page.load_working_papers()
                                except Exception: pass

                    if hasattr(self, 'workspace_panel'):
                        self.workspace_panel.refresh_workspace_state()
                    if hasattr(self, 'needs_attention_panel'):
                        self.needs_attention_panel.refresh_attention_items(target_id)

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
        """Initializes global search and navigation keyboard shortcuts."""
        self._setup_search_shortcut()
        self._setup_nav_shortcuts()

    def show_keyboard_shortcuts_dialog(self):
        shortcuts_text = """
<b>FinAuditPro Desktop Keyboard Shortcuts:</b><br/><br/>
• <b>Alt + 1</b> : Master Dashboard Overview<br/>
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

class AuditProgressChart(QFrame):
    """Enterprise Audit Progress Trend Chart with Empty State support."""
    def __init__(self, projects: list = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("auditProgressCard")
        is_dark = ThemeManager().is_dark
        card_bg = "#222224" if is_dark else "#FFFFFF"
        card_border = "#2E2E32" if is_dark else "#E5E5EA"
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        self.setStyleSheet(f"""
            QFrame#auditProgressCard {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 14, 18, 14)
        self.layout.setSpacing(10)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("Audit Progress Trend")
        title_lbl.setStyleSheet(f"font-weight: 700; font-size: 15px; color: {text_clr}; border: none;")

        period_combo = QComboBox()
        period_combo.addItems(["Last 6 Months", "FY 2025-26", "All Time"])
        period_combo.setFixedWidth(130)
        period_combo.setObjectName("periodCombo")

        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(period_combo)
        self.layout.addLayout(h_layout)

        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.container_widget, 1)

        self.update_data(projects or [])

    def update_data(self, projects: list):
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        is_dark = ThemeManager().is_dark
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        sub_clr = "#8E8E93" if is_dark else "#86868B"

        if not projects:
            empty_box = QFrame()
            empty_box.setStyleSheet("background: transparent; border: none;")
            eb_layout = QVBoxLayout(empty_box)
            eb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            eb_layout.setSpacing(4)

            t1 = QLabel("No completed audits yet")
            t1.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {text_clr}; border: none; background: transparent; background-color: transparent;")
            t1.setAlignment(Qt.AlignmentFlag.AlignCenter)

            t2 = QLabel("Your audit activity and lifecycle progress trends will appear here.")
            t2.setStyleSheet(f"font-size: 12px; color: {sub_clr}; border: none; background: transparent; background-color: transparent;")
            t2.setAlignment(Qt.AlignmentFlag.AlignCenter)

            eb_layout.addWidget(t1)
            eb_layout.addWidget(t2)
            self.container_layout.addWidget(empty_box)
            return

        chart = QChart()
        chart.legend().hide()
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 4, 0, 4))

        series = QSplineSeries()
        series.setPen(QPen(QColor("#0A84FF" if is_dark else "#007AFF"), 2.5))

        from datetime import datetime as _dt
        now = _dt.now()
        months = []
        for i in range(5, -1, -1):
            m = now.month - i
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            months.append(_dt(y, m, 1).strftime("%b"))

        data_points = [0] * 6
        for idx, p in enumerate(projects[:6]):
            data_points[idx] = 100 if getattr(p, 'status', '') == "Completed" else 60 if getattr(p, 'status', '') == "Execution" else 30

        for i, val in enumerate(data_points):
            series.append(i, val)

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        label_clr = QColor("#8E8E93") if ThemeManager().is_dark else QColor("#6E6E73")
        grid_clr = QColor("#38383A") if ThemeManager().is_dark else QColor("#E5E5EA")
        axis_x.setLabelsColor(label_clr)
        axis_x.setGridLineColor(grid_clr)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setLabelsColor(label_clr)
        axis_y.setGridLineColor(grid_clr)
        axis_y.setTickCount(5)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.container_layout.addWidget(chart_view)

    def closeEvent(self, event):
        """Clean shutdown handler to stop active timers and prevent PySide6 segmentation faults on exit."""
        try:
            if hasattr(self, 'timer') and self.timer:
                self.timer.stop()
        except Exception:
            pass
        event.accept()
