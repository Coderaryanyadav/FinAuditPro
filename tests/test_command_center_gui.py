"""Automated PySide6 GUI tests for the operational Practice Command Center (DashboardView)."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.practice_dashboard_service import PracticeDashboardService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.dashboard_view import DashboardView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_cc_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_dashboard_view_empty_state_rendering(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test DashboardView renders empty state widgets when initialized with an empty database."""
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)
    dash_svc = PracticeDashboardService(db_manager)

    view = DashboardView(firm_svc, client_svc, eng_svc, matrix_svc, practice_dashboard_service=dash_svc)
    view.show()

    assert view.isVisible()
    assert view.lbl_firm_name.text() == "CA Practice"
    assert view.card_clients.value_lbl.text() == "0"
    assert view.card_active.value_lbl.text() == "0"
    assert view.card_completed.value_lbl.text() == "0"

    view.close()


@pytest.mark.gui
def test_dashboard_view_populated_metrics(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test DashboardView displays operational practice metrics when seeded with data."""
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)
    dash_svc = PracticeDashboardService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Pinnacle CA Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Pinnacle Retail Pvt Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    view = DashboardView(firm_svc, client_svc, eng_svc, matrix_svc, practice_dashboard_service=dash_svc)
    view.set_firm(firm)
    view.show()

    assert view.isVisible()
    assert view.lbl_firm_name.text() == "Pinnacle CA Firm"
    assert view.card_clients.value_lbl.text() == "1"
    assert view.card_active.value_lbl.text() == "1"

    view.close()


@pytest.mark.gui
def test_dashboard_view_quick_action_signals(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test that quick action buttons emit navigation signals."""
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)
    dash_svc = PracticeDashboardService(db_manager)

    view = DashboardView(firm_svc, client_svc, eng_svc, matrix_svc, practice_dashboard_service=dash_svc)
    view.show()

    clients_emitted = []
    engagements_emitted = []
    documents_emitted = []

    view.navigate_to_clients.connect(lambda: clients_emitted.append(True))
    view.navigate_to_engagements.connect(lambda: engagements_emitted.append(True))
    view.navigate_to_documents.connect(lambda: documents_emitted.append(True))

    view.card_clients.clicked.emit()
    assert len(clients_emitted) == 1

    view.card_active.clicked.emit()
    assert len(engagements_emitted) == 1

    view.close()
