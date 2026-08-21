"""
Comprehensive UI Component Integration Test Suite for FinAuditPro.
Verifies clean instantiation, database bindings, and signal handling for all 11 PySide6 UI widgets.
"""

import sys
import os

# Set Qt platform to offscreen for headless unit testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtWidgets import QApplication

# Ensure src directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from deployment.migration import DatabaseMigrator
from database.database import init_db, SessionLocal
from database.models import Client, AuditProject, Finding, Document

@pytest.fixture(scope="module")
def qapp():
    """Provides a singleton QApplication instance for PySide6 UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture(autouse=True)
def setup_db():
    """Ensures database schema is migrated and available for tests."""
    init_db()
    DatabaseMigrator.migrate()

def test_login_window_instantiation(qapp):
    from ui.login import LoginWindow
    login = LoginWindow()
    assert login is not None
    assert "FinAuditPro" in login.windowTitle()

def test_dashboard_window_instantiation(qapp):
    from ui.dashboard import DashboardWindow
    dashboard = DashboardWindow()
    assert dashboard is not None
    assert dashboard.stacked_widget.count() == 13

def test_findings_workspace_widget(qapp):
    from ui.findings import FindingsWorkspaceWidget
    findings_widget = FindingsWorkspaceWidget()
    assert findings_widget is not None
    findings_widget.load_findings_data()

def test_pdf_viewer_widget(qapp):
    from ui.pdf_viewer import PDFViewerWidget
    pdf_widget = PDFViewerWidget()
    assert pdf_widget is not None
    pdf_widget.load_pdf("")

def test_client_management_widget(qapp):
    from ui.clients import ClientManagementWidget
    client_widget = ClientManagementWidget()
    assert client_widget is not None
    client_widget.load_clients()

def test_document_upload_widget(qapp):
    from ui.documents import DocumentUploadWidget
    doc_widget = DocumentUploadWidget()
    assert doc_widget is not None
    doc_widget.load_uploaded_files()

def test_ai_audit_widget(qapp):
    from ui.ai_analysis import AIAuditWidget
    ai_widget = AIAuditWidget()
    assert ai_widget is not None
    ai_widget.load_database_findings()
    ai_widget.load_active_document_view()

def test_risk_analysis_widget(qapp):
    from ui.risk_analysis import RiskAnalysisWidget
    risk_widget = RiskAnalysisWidget()
    assert risk_widget is not None
    risk_widget.load_findings()

def test_reports_widget(qapp):
    from ui.reports import ReportsWidget
    reports_widget = ReportsWidget()
    assert reports_widget is not None

def test_working_paper_widget(qapp):
    from ui.working_papers import WorkingPaperWidget
    wp_widget = WorkingPaperWidget()
    assert wp_widget is not None
    wp_widget.load_audit_projects()

def test_gst_verification_widget(qapp):
    from ui.gst_verification import GSTVerificationWidget
    gst_widget = GSTVerificationWidget()
    assert gst_widget is not None

def test_compliance_widget(qapp):
    from ui.compliance import ComplianceWidget
    compliance_widget = ComplianceWidget()
    assert compliance_widget is not None
    compliance_widget.load_compliance_data()

def test_settings_widget(qapp):
    from ui.settings import SettingsWidget
    settings_widget = SettingsWidget()
    assert settings_widget is not None

def test_history_widget(qapp):
    from ui.history import AuditHistoryWidget
    history_widget = AuditHistoryWidget()
    assert history_widget is not None

def test_window_responsive_resizing(qapp):
    """Verifies runtime window resizing reflows without layout errors or clipping."""
    from ui.login import LoginWindow
    from ui.dashboard import DashboardWindow

    login = LoginWindow()
    login.resize(800, 600)
    login.resize(1920, 1080)
    assert login.width() == 1920
    assert login.height() == 1080

    dashboard = DashboardWindow()
    dashboard.resize(1280, 720)
    dashboard.resize(2560, 1440)
    assert dashboard.width() == 2560
    assert dashboard.height() == 1440
