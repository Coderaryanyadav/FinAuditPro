"""Automated PySide6 GUI tests for ClientWorkspaceView."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.client_workspace_service import ClientWorkspaceService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.client_workspace_view import ClientWorkspaceView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_client_ws_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_client_workspace_view_rendering_and_tabs(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test ClientWorkspaceView renders persistent header and switches across all 8 sub-tabs."""
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    workspace_svc = ClientWorkspaceService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="GUI WS Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="GUI Workspace Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    view = ClientWorkspaceView(workspace_svc)
    view.set_client(client.id)
    view.show()

    assert view.isVisible()
    assert view.lbl_client_name.text() == "GUI Workspace Client"
    assert len(view.tab_buttons) == 8

    # Switch across sub-tabs
    for tab_i in range(8):
        view._on_sub_tab_clicked(tab_i)
        assert view.current_tab_idx == tab_i
        assert view.stack.currentIndex() == tab_i

    view.close()
