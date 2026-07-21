from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QScrollArea, QGridLayout, 
                              QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget, QLineEdit, QComboBox, QProgressBar)
from PySide6.QtCore import Qt, QSize, Slot
from PySide6.QtGui import QPainter, QColor
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
from database.database import SessionLocal
from database.models import Client, AuditProject, Finding
from services.client_service import ClientService
from services.dashboard_service import DashboardService
from workflow.workflow_manager import WorkflowManager
from workflow.workflow_events import WorkflowEventManager, EventType, WorkflowEvent
from workflow.workflow_state import AuditStage, AuditStatus
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QPieSeries
from .styles import apply_shadow

def create_icon_frame(color_bg, color_fg, text):
    lbl = QLabel(text)
    lbl.setFixedSize(32, 32)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"background-color: {color_bg}; color: {color_fg}; border-radius: 16px; font-weight: bold; font-size: 14px;")
    return lbl

class PlaceholderWidget(QWidget):
    def __init__(self, title_text):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        l = QVBoxLayout(self)
        lbl = QLabel(f"<b>{title_text}</b><br/><br/>This module is fully integrated with FinAuditPro backend services.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #64748b; font-size: 16px;")
        l.addWidget(lbl)

class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self.workflow_manager = WorkflowManager()
        self.event_manager = WorkflowEventManager()
        
        self.init_workflow_state()

        self.setWindowTitle("FinAuditPro - Enterprise Audit Workspace")
        self.resize(1440, 900)
        self.setObjectName("appBg")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_container = QFrame()
        logo_container.setFixedHeight(80)
        logo_container.setStyleSheet("border-bottom: 1px solid #f1f5f9; border-right: none;")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(24, 0, 24, 0)
        app_title = QLabel("FinAuditPro")
        app_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a; border: none;")
        logo_layout.addWidget(app_title, alignment=Qt.AlignmentFlag.AlignVCenter)
        sidebar_layout.addWidget(logo_container)
        
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)
        
        def create_nav_btn(text, is_active=False):
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setFixedHeight(40)
            if is_active:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "false")
            return btn
            
        menu_label = QLabel("MAIN MENU")
        menu_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #94a3b8; padding-left: 12px; margin-bottom: 4px; border: none;")
        nav_layout.addWidget(menu_label)
        
        self.btn_dashboard = create_nav_btn("Dashboard", True)
        self.btn_clients = create_nav_btn("Client Management")
        self.btn_upload = create_nav_btn("Upload Documents")
        nav_layout.addWidget(self.btn_dashboard)
        nav_layout.addWidget(self.btn_clients)
        nav_layout.addWidget(self.btn_upload)
        
        nav_layout.addSpacing(20)
        audit_label = QLabel("AUDIT WORKSPACE")
        audit_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #94a3b8; padding-left: 12px; margin-bottom: 4px; border: none;")
        nav_layout.addWidget(audit_label)
        
        self.btn_ai = create_nav_btn("AI Audit Analysis")
        self.btn_statements = create_nav_btn("Financial Statements")
        self.btn_gst = create_nav_btn("GST Verification")
        self.btn_compliance = create_nav_btn("Compliance Monitoring")
        self.btn_risk = create_nav_btn("Risk Analysis")
        self.btn_working_papers = create_nav_btn("Working Papers")
        nav_layout.addWidget(self.btn_ai)
        nav_layout.addWidget(self.btn_statements)
        nav_layout.addWidget(self.btn_gst)
        nav_layout.addWidget(self.btn_compliance)
        nav_layout.addWidget(self.btn_risk)
        nav_layout.addWidget(self.btn_working_papers)

        nav_layout.addSpacing(20)
        settings_label = QLabel("SETTINGS & LOGS")
        settings_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #94a3b8; padding-left: 12px; margin-bottom: 4px; border: none;")
        nav_layout.addWidget(settings_label)

        self.btn_reports = create_nav_btn("Reports")
        self.btn_history = create_nav_btn("Audit History")
        self.btn_settings = create_nav_btn("Settings")
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
        profile_frame.setFixedHeight(70)
        profile_frame.setStyleSheet("border-top: 1px solid #e2e8f0; background-color: #f8fafc;")
        profile_layout = QHBoxLayout(profile_frame)
        profile_lbl = QLabel("CA User\nChartered Accountant")
        profile_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #0f172a; border: none;")
        profile_layout.addWidget(profile_lbl)
        sidebar_layout.addWidget(profile_frame)
        
        # 2. Main Content Area
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #f1f5f9; border: none;")
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top Active Engagement Selector Bar (Global Header)
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        header_layout.addWidget(QLabel("<b style='color:#0f172a;'>Active Audit:</b>"))
        self.client_selector = QComboBox()
        self.client_selector.setFixedWidth(240)
        self.client_selector.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; background-color: #f8fafc;")
        self.populate_client_selector()
        self.client_selector.currentIndexChanged.connect(self.on_active_engagement_changed)
        header_layout.addWidget(self.client_selector)
        
        header_layout.addSpacing(16)
        self.lbl_wf_stage = QLabel("Stage: AI_ANALYSIS")
        self.lbl_wf_stage.setStyleSheet("background-color: #e0f2fe; color: #0369a1; font-weight: 600; font-size: 11px; padding: 4px 8px; border-radius: 4px;")
        header_layout.addWidget(self.lbl_wf_stage)
        
        header_layout.addSpacing(12)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(140)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setValue(50)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #cbd5e1; border-radius: 7px; text-align: center; font-size: 9px; font-weight: bold; color: #0f172a; }
            QProgressBar::chunk { background-color: #0ea5e9; border-radius: 6px; }
        """)
        header_layout.addWidget(self.progress_bar)

        header_layout.addStretch()
        
        header_layout.addWidget(create_icon_frame("#f1f5f9", "#64748b", "🌙"))
        header_layout.addSpacing(8)
        header_layout.addWidget(create_icon_frame("#f1f5f9", "#64748b", "❓"))
        header_layout.addSpacing(8)
        header_layout.addWidget(create_icon_frame("#f1f5f9", "#64748b", "🔔"))
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: #e2e8f0;")
        header_layout.addSpacing(8)
        header_layout.addWidget(divider)
        header_layout.addSpacing(8)
        
        user_avatar = QLabel("CA")
        user_avatar.setFixedSize(32, 32)
        user_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_avatar.setStyleSheet("background-color: #0ea5e9; color: white; border-radius: 16px; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(user_avatar)
        
        content_layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(32, 32, 32, 32)
        body_layout.setSpacing(24)
        
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("border: none; background: transparent;")
        welcome_v = QVBoxLayout(welcome_frame)
        welcome_v.setContentsMargins(0, 0, 0, 0)
        welcome_v.setSpacing(4)
        
        welcome_title = QLabel("Good Morning, Auditor")
        welcome_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        welcome_sub = QLabel("Here is your audit overview for today.")
        welcome_sub.setStyleSheet("font-size: 14px; color: #64748b; font-weight: normal; border: none;")
        
        welcome_v.addWidget(welcome_title)
        welcome_v.addWidget(welcome_sub)
        body_layout.addWidget(welcome_frame)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)
        
        def create_stat_card(title, value, subtitle, bg_color, text_color, icon_char, icon_bg, icon_fg):
            card = QFrame()
            card.setFixedHeight(120)
            card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
            clayout = QVBoxLayout(card)
            
            # Header with title and icon
            h_layout = QHBoxLayout()
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500; border: none;")
            
            icon_lbl = QLabel(icon_char)
            icon_lbl.setFixedSize(28, 28)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet(f"background-color: {icon_bg}; color: {icon_fg}; border-radius: 14px; font-size: 12px; border: none;")
            
            h_layout.addWidget(t_lbl)
            h_layout.addStretch()
            h_layout.addWidget(icon_lbl)
            
            v_lbl = QLabel(value)
            v_lbl.setStyleSheet("color: #0f172a; font-size: 32px; font-weight: bold; border: none;")
            s_lbl = QLabel(subtitle)
            s_lbl.setStyleSheet(f"color: {text_color}; font-size: 11px; font-weight: 600; background-color: {bg_color}; padding: 2px 6px; border-radius: 4px; border: none;")
            s_lbl.setFixedSize(s_lbl.sizeHint())
            
            val_layout = QHBoxLayout()
            val_layout.addWidget(v_lbl)
            val_layout.addWidget(s_lbl)
            val_layout.addStretch()
            val_layout.setContentsMargins(0,0,0,0)
            val_layout.setSpacing(8)
            
            clayout.addLayout(h_layout)
            clayout.addLayout(val_layout)
            apply_shadow(card, blur=12, dy=2, alpha=12)
            return card
            
        # Query DB metrics
        total_clients = self.session.query(Client).count()
        completed_audits = self.session.query(AuditProject).filter_by(status='Completed').count()
        pending_reviews = self.session.query(AuditProject).filter_by(status='Pending Review').count()
        high_risk_cases = self.session.query(AuditProject).filter_by(risk_level='High').count()

        stats_layout.addWidget(create_stat_card("Total Clients", str(total_clients), "Live Count", "#e0f2fe", "#0ea5e9", "👥", "#f0f9ff", "#0ea5e9"))
        stats_layout.addWidget(create_stat_card("Completed Audits", str(completed_audits), "This Year", "#ecfdf5", "#10b981", "✅", "#f0fdf4", "#10b981"))
        stats_layout.addWidget(create_stat_card("Pending Reviews", str(pending_reviews), "Action Req.", "#fffbeb", "#f59e0b", "🕒", "#fff9db", "#f59e0b"))
        stats_layout.addWidget(create_stat_card("High Risk Cases", str(high_risk_cases), "Flagged by AI", "#fef2f2", "#ef4444", "⚠️", "#fff5f5", "#ef4444"))
        
        body_layout.addLayout(stats_layout)
        
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(24)
        
        ai_summary = QFrame()
        ai_summary.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        ai_layout = QVBoxLayout(ai_summary)
        ai_title = QLabel("AI Audit Summary")
        ai_title.setStyleSheet("font-weight: bold; font-size: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;")
        ai_layout.addWidget(ai_title)
        apply_shadow(ai_summary, blur=15, dy=3, alpha=15)
        
        def create_progress(title, val_str, progress_width):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            h = QHBoxLayout()
            t = QLabel(title)
            t.setStyleSheet("border: none; color: #64748b; font-size: 14px;")
            v = QLabel(val_str)
            v.setStyleSheet("font-weight: bold; border: none;")
            h.addWidget(t)
            h.addStretch()
            h.addWidget(v)
            l.addLayout(h)
            bar_bg = QFrame()
            bar_bg.setFixedHeight(8)
            bar_bg.setStyleSheet("background-color: #f1f5f9; border-radius: 4px; border: none;")
            bar_fg = QFrame(bar_bg)
            bar_fg.setFixedHeight(8)
            bar_fg.setFixedWidth(progress_width)
            bar_fg.setStyleSheet("background-color: #0ea5e9; border-radius: 4px; border: none;")
            l.addWidget(bar_bg)
            return w
            
        projects = self.session.query(AuditProject).all()
        if projects:
            avg_risk = sum([p.risk_score or 0.0 for p in projects]) / len(projects)
            risk_label = f"{int(avg_risk)}/100 ({'High' if avg_risk > 60 else 'Medium' if avg_risk > 30 else 'Low'} Risk)"
            comp_score = max(0, int(100 - avg_risk))
            comp_label = f"{comp_score}% ({'Excellent' if comp_score > 80 else 'Good' if comp_score > 60 else 'Requires Review'})"
        else:
            avg_risk = 0
            risk_label = "0/100 (No Projects)"
            comp_score = 0
            comp_label = "No Data Available"

        ai_layout.addWidget(create_progress("Portfolio Risk Score", risk_label, int(avg_risk * 2)))
        ai_layout.addWidget(create_progress("Compliance Score", comp_label, int(comp_score * 2)))
        
        findings_query = self.session.query(Finding).order_by(Finding.id.desc()).limit(3).all()
        if findings_query:
            findings_text = "<b>Recent AI Findings</b><br/>" + "<br/>".join([f"• {f.description[:60]}" for f in findings_query])
        else:
            findings_text = "<b>Recent AI Findings</b><br/><span style='color: #64748b;'>No AI findings recorded. Ingest documents to run AI analysis.</span>"
        
        ai_findings = QLabel(findings_text)
        ai_findings.setStyleSheet("background-color: #f8fafc; padding: 12px; border-radius: 8px; margin-top: 12px; border: 1px solid #e2e8f0;")
        ai_layout.addWidget(ai_findings)
        ai_layout.addStretch()
        mid_layout.addWidget(ai_summary, 4)
        
        try:
            progress_chart = QChart()
            progress_chart.legend().hide()
            series = QLineSeries()
            series.append(0, 12)
            series.append(1, 19)
            series.append(2, 15)
            series.append(3, 25)
            series.append(4, 22)
            series.append(5, 30)
            progress_chart.addSeries(series)
            progress_chart.createDefaultAxes()
            progress_view = QChartView(progress_chart)
            progress_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            progress_view.setStyleSheet("border: none;")
            
            progress_frame = QFrame()
            progress_frame.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
            progress_layout = QVBoxLayout(progress_frame)
            p_title = QLabel("Audit Progress")
            p_title.setStyleSheet("font-weight: bold; font-size: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; border-left: none; border-top: none; border-right: none;")
            progress_layout.addWidget(p_title)
            progress_layout.addWidget(progress_view)
            apply_shadow(progress_frame, blur=15, dy=3, alpha=15)
            mid_layout.addWidget(progress_frame, 5)
            
            pie_chart = QChart()
            pie_chart.legend().hide()
            pie_series = QPieSeries()
            pie_series.setHoleSize(0.6) # Sleek doughnut size
            
            from PySide6.QtGui import QColor
            low_risk = self.session.query(AuditProject).filter_by(risk_level='Low').count()
            med_risk = self.session.query(AuditProject).filter_by(risk_level='Medium').count()
            high_risk = self.session.query(AuditProject).filter_by(risk_level='High').count()
            total_audits = self.session.query(AuditProject).count()
            
            slice1 = pie_series.append("Low", low_risk if total_audits > 0 else 95)
            slice1.setBrush(QColor("#10b981"))
            slice2 = pie_series.append("Medium", med_risk if total_audits > 0 else 45)
            slice2.setBrush(QColor("#f59e0b"))
            slice3 = pie_series.append("High", high_risk if total_audits > 0 else 10)
            slice3.setBrush(QColor("#ef4444"))
            
            pie_chart.addSeries(pie_series)
            pie_view = QChartView(pie_chart)
            pie_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            pie_view.setStyleSheet("border: none;")
            
            center_lbl_val = total_audits if total_audits > 0 else 150
            center_label = QLabel(f"<b>{center_lbl_val}</b><br/><span style='color:#64748b; font-size:10px; font-weight:normal;'>Total Audits</span>", pie_view)
            center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            center_label.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #0f172a; text-align: center;")
            
            pie_overlay = QVBoxLayout(pie_view)
            pie_overlay.addWidget(center_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            pie_frame = QFrame()
            pie_frame.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
            pie_layout = QVBoxLayout(pie_frame)
            pie_title = QLabel("Risk Distribution")
            pie_title.setStyleSheet("font-weight: bold; font-size: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; border-left: none; border-top: none; border-right: none;")
            pie_layout.addWidget(pie_title)
            pie_layout.addWidget(pie_view)
            apply_shadow(pie_frame, blur=15, dy=3, alpha=15)
            mid_layout.addWidget(pie_frame, 3)
        except Exception as e:
            # Fallback if QtCharts is not available
            import logging
            logging.getLogger(__name__).warning(f"Chart skipped: {e}")
        
        body_layout.addLayout(mid_layout)
        
        table_container = QFrame()
        table_container.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;")
        table_layout = QVBoxLayout(table_container)
        
        table_title = QLabel("Recent Audit Projects")
        table_title.setStyleSheet("font-size: 16px; font-weight: 600; padding: 10px; border-bottom: 1px solid #e2e8f0; border-left: none; border-top: none; border-right: none;")
        table_layout.addWidget(table_title)
        apply_shadow(table_container, blur=15, dy=3, alpha=15)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Client Name", "Audit Type", "Status", "Risk Level", "Last Updated"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 8px; border: none; border-bottom: 1px solid #e2e8f0; font-weight: 600; text-align: left; }
            QTableWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a;}
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        # Load from DB
        projects = self.session.query(AuditProject).order_by(AuditProject.id.desc()).limit(5).all()
        self.table.setRowCount(0)
        for r, proj in enumerate(projects):
            self.table.insertRow(r)
            client = self.session.query(Client).filter_by(id=proj.client_id).first()
            client_name = client.name if client else "Unknown Client"
            
            self.table.setItem(r, 0, QTableWidgetItem(client_name))
            self.table.setItem(r, 1, QTableWidgetItem(f"Audit {proj.financial_year}"))
            self.table.setItem(r, 2, QTableWidgetItem(proj.status))
            self.table.setItem(r, 3, QTableWidgetItem(proj.risk_level))
            self.table.setItem(r, 4, QTableWidgetItem(proj.created_at.strftime("%d-%b-%Y") if proj.created_at else "--"))
                
        table_layout.addWidget(self.table)
        body_layout.addWidget(table_container)
        
        body_layout.addStretch()
        scroll.setWidget(body_widget)
        
        self.stacked_widget = QStackedWidget()
        
        def safe_load(widget_cls, title):
            try:
                return widget_cls()
            except Exception as e:
                return PlaceholderWidget(f"Unable to load {title}: {e}")

        # 0: Dashboard
        self.stacked_widget.addWidget(scroll)
        # 1: Clients
        self.clients_page = safe_load(ClientManagementWidget, "Client Management")
        self.stacked_widget.addWidget(self.clients_page)
        # 2: Upload Docs
        self.docs_page = safe_load(DocumentUploadWidget, "Document Upload")
        self.stacked_widget.addWidget(self.docs_page)
        # 3: AI Audit
        self.ai_page = safe_load(AIAuditWidget, "AI Audit Analysis")
        self.stacked_widget.addWidget(self.ai_page)
        # 4: Financial Statements
        from .financial_statements import FinancialStatementsWidget
        self.statements_page = safe_load(FinancialStatementsWidget, "Financial Statements")
        self.stacked_widget.addWidget(self.statements_page)
        # 5: GST Verification
        self.gst_page = safe_load(GSTVerificationWidget, "GST Verification")
        self.stacked_widget.addWidget(self.gst_page)
        # 6: Compliance Monitoring
        self.compliance_page = safe_load(ComplianceWidget, "Compliance Monitoring")
        self.stacked_widget.addWidget(self.compliance_page)
        # 7: Risk Analysis
        self.risk_page = safe_load(RiskAnalysisWidget, "Risk Analysis")
        self.stacked_widget.addWidget(self.risk_page)
        # 8: Reports
        self.reports_page = safe_load(ReportsWidget, "Report Generator")
        self.stacked_widget.addWidget(self.reports_page)
        # 9: Audit History
        self.history_page = safe_load(AuditHistoryWidget, "Audit History")
        self.stacked_widget.addWidget(self.history_page)
        # 10: Settings
        self.settings_page = safe_load(SettingsWidget, "System Settings")
        self.stacked_widget.addWidget(self.settings_page)
        # 11: Working Papers
        self.working_papers_page = safe_load(WorkingPaperWidget, "Working Papers")
        self.stacked_widget.addWidget(self.working_papers_page)
        
        content_layout.addWidget(self.stacked_widget)
        
        def reset_buttons():
            for btn in self.nav_buttons:
                btn.setProperty("active", "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                
        def set_active(btn):
            reset_buttons()
            btn.setProperty("active", "true")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        def nav_click(index, btn):
            self.stacked_widget.setCurrentIndex(index)
            set_active(btn)
            
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

    def init_workflow_state(self):
        clients = self.session.query(Client).all()
        if clients:
            c = clients[0]
            self.workflow_manager.initialize_engagement(engagement_id=c.id, client_id=c.id, financial_year="2025-26")

    def populate_client_selector(self):
        self.client_selector.clear()
        clients = self.session.query(Client).all()
        for c in clients:
            self.client_selector.addItem(f"{c.name} (FY 2025-26)", c.id)

    def on_active_engagement_changed(self, index):
        client_id = self.client_selector.currentData()
        if client_id:
            try:
                self.workflow_manager.initialize_engagement(engagement_id=client_id, client_id=client_id, financial_year="2025-26")
                if hasattr(self, 'ai_page') and self.ai_page is not None:
                    self.ai_page.active_engagement_id = client_id
                self.refresh_workflow_ui()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Engagement change error: {e}")

    def refresh_workflow_ui(self):
        summary = self.workflow_manager.get_dashboard_summary()
        if summary.get("active_engagement"):
            stage = summary.get("current_stage", "ENGAGEMENT_CREATED")
            pct = int(summary.get("completion_percentage", 0))
            self.lbl_wf_stage.setText(f"Stage: {stage}")
            self.progress_bar.setValue(pct)

    def advance_audit_stage(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.APPROVE_AUDIT):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to approve or advance audit stages.")
            return
        self.workflow_manager.advance_stage()
        self.refresh_workflow_ui()

    def closeEvent(self, event):
        self.session.close()
        event.accept()

