"""GUI unit tests for Financial Data Workspace PySide6 components."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.financial_dtos import ImportDatasetDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_analytics_service import FinancialAnalyticsService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.financial_data_view import FinancialDataView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_fin_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_financial_data_view_rendering(
    qapp: QApplication, db_manager: DatabaseManager, tmp_path
) -> None:
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    data_svc = FinancialDataService(db_manager)
    analytics_svc = FinancialAnalyticsService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="GUI Fin Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="GUI Fin Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    csv_file = tmp_path / "gui_test_gl.csv"
    csv_file.write_text("Date,Amount,Account\n2026-04-01,100000,Sales Revenue", encoding="utf-8")
    data_svc.import_financial_dataset(
        ImportDatasetDTO(engagement_id=eng.id, dataset_name="GUI GL", file_path=str(csv_file))
    )

    view = FinancialDataView(client_svc, eng_svc, data_svc, analytics_svc)
    view.set_engagement(eng.id)

    assert view.dataset_combo.count() == 1
    assert view.records_table.rowCount() == 1
    assert view.import_btn.isEnabled()
