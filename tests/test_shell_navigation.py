"""Automated PySide6 UI tests for the redesigned FinAuditPro Global Application Shell."""

import sys
from collections.abc import Generator

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import RoleEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_shell.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_shell_initialization_and_header_context(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test that MainWindow initializes with the global header active context and engagement selection."""
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Shell Test Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Shell Test Client Inc"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    window = MainWindow(db_manager)
    window.show()

    assert window.isVisible()
    assert window.current_firm is not None
    assert window.current_firm.id == firm.id
    assert window.current_client is not None
    assert window.current_client.id == client.id
    assert window.current_engagement is not None
    assert window.current_engagement.id == eng.id
    assert window.active_engagement_id == eng.id

    window.close()


@pytest.mark.gui
def test_primary_sidebar_category_navigation(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test navigation across all 7 primary categories and sub-tab selection."""
    window = MainWindow(db_manager)
    window.show()

    # 1. Command Center (Category 0)
    window._on_category_changed(0)
    assert window.current_category_idx == 0
    assert window.stack.currentWidget() == window.view_dashboard

    # 2. Inbox (Category 1)
    window._on_category_changed(1)
    assert window.current_category_idx == 1
    assert window.stack.currentWidget() == window.view_inbox

    # Switch sub-tab to Queries
    window._on_sub_tab_selected("queries")
    assert window.stack.currentWidget() == window.view_queries

    # 3. Clients & Firms (Category 2)
    window._on_category_changed(2)
    assert window.current_category_idx == 2
    assert window.stack.currentWidget() == window.view_clients

    # 4. Work & Compliance (Category 3)
    window._on_category_changed(3)
    assert window.current_category_idx == 3
    assert window.stack.currentWidget() == window.view_work_center

    window._on_sub_tab_selected("compliance")
    assert window.stack.currentWidget() == window.view_compliance

    # 5. Audit Engagement (Category 4)
    window._on_category_changed(4)
    assert window.current_category_idx == 4
    assert window.stack.currentWidget() == window.view_guided_workflow

    window._on_sub_tab_selected("working_papers")
    assert window.stack.currentWidget() == window.view_working_papers

    # 6. AI Assistant (Category 5)
    window._on_category_changed(5)
    assert window.current_category_idx == 5
    assert window.stack.currentWidget() == window.view_ai_assistant

    # 7. System (Category 6)
    window._on_category_changed(6)
    assert window.current_category_idx == 6
    assert window.stack.currentWidget() == window.view_settings

    window.close()


@pytest.mark.gui
def test_legacy_button_handles_and_routing_aliases(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test that all self.btn_* handles trigger their respective view navigation cleanly."""
    window = MainWindow(db_manager)
    window.show()

    # Test legacy btn_working_papers click
    window.btn_working_papers.click()
    assert window.stack.currentWidget() == window.view_working_papers
    assert window.current_category_idx == 4  # Category 4: Audit Engagement

    # Test legacy btn_compliance click
    window.btn_compliance.click()
    assert window.stack.currentWidget() == window.view_compliance
    assert window.current_category_idx == 3  # Category 3: Work & Compliance

    # Test legacy btn_clients click
    window.btn_clients.click()
    assert window.stack.currentWidget() == window.view_clients
    assert window.current_category_idx == 2  # Category 2: Clients

    # Test legacy btn_settings click
    window.btn_settings.click()
    assert window.stack.currentWidget() == window.view_settings
    assert window.current_category_idx == 6  # Category 6: System

    window.close()


@pytest.mark.gui
def test_sidebar_collapse_toggle(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test sidebar collapse and expand toggle functionality."""
    window = MainWindow(db_manager)
    window.show()

    assert window.sidebar.is_collapsed is False
    assert window.sidebar.width() == 220

    # Toggle to collapse
    window.sidebar.toggle_collapse_state()
    assert window.sidebar.is_collapsed is True
    assert window.sidebar.width() == 60

    # Toggle back to expand
    window.sidebar.toggle_collapse_state()
    assert window.sidebar.is_collapsed is False
    assert window.sidebar.width() == 220

    window.close()


@pytest.mark.gui
def test_ai_copilot_drawer_toggle(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test AI Copilot drawer visibility toggle."""
    window = MainWindow(db_manager)
    window.show()

    assert window.ai_drawer.isVisible() is False

    # Toggle drawer open
    window._toggle_ai_drawer()
    assert window.ai_drawer.isVisible() is True

    # Toggle drawer close
    window._toggle_ai_drawer()
    assert window.ai_drawer.isVisible() is False

    window.close()


@pytest.mark.gui
def test_rbac_user_session_display(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test RBAC session application and sidebar user profile rendering."""
    window = MainWindow(db_manager)
    window.show()

    session = UserSession(
        user_id="u-partner-1", username="partner.shah@finaudit.com", role=RoleEnum.PARTNER
    )
    window.current_user_session = session
    window._apply_user_session()

    assert window.sidebar.lbl_user_name.text() == "Partner.Shah"
    assert "PARTNER" in window.sidebar.lbl_user_role.text().upper() or "Partner" in window.sidebar.lbl_user_role.text()

    window.close()
