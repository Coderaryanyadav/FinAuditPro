"""GUI unit tests for PySide6 components."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
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
    db_path = tmp_path / "test_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_main_window_initialization_and_rendering(qapp: QApplication, db_manager: DatabaseManager) -> None:
    # Seed DB with initial data
    firm_service = FirmService(db_manager)
    client_service = ClientService(db_manager)
    engagement_service = EngagementService(db_manager)

    firm = firm_service.create_firm(CreateFirmDTO(name="GUI Audit Firm"))
    client = client_service.create_client(CreateClientDTO(firm_id=firm.id, name="GUI Client Inc"))
    eng = engagement_service.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )
    assert eng.id is not None

    window = MainWindow(db_manager)
    window.show()

    assert window.isVisible()
    assert window.active_engagement_id is not None or window.firm_service.list_firms()

    window.close()
