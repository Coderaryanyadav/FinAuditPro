"""GUI unit tests for Audit Matrix Workspace PySide6 components."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.audit_matrix_dtos import CreateRiskDTO
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.audit_matrix_view import AuditMatrixView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_matrix_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_audit_matrix_view_rendering(qapp: QApplication, db_manager: DatabaseManager) -> None:
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    mat_svc = MaterialityService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="GUI Matrix Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="GUI Matrix Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-001",
            category="Revenue",
            description="GUI Risk Test",
        )
    )

    view = AuditMatrixView(eng_svc, mat_svc, matrix_svc)
    view.set_engagement(eng.id)

    assert view.risks_table.rowCount() == 1
    assert view.tabs.count() == 4
