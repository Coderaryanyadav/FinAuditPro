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
from finauditpro.infrastructure.first_run import initialize_database
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
    return initialize_database(db_path)



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


@pytest.mark.gui
def test_phase_a_dialogs_rendering(qapp: QApplication, db_manager: DatabaseManager) -> None:
    from finauditpro.application.services.account_mapping_service import AccountMappingService
    from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
    from finauditpro.ui.dialogs.account_mapping_dialog import AccountMappingDialog
    from finauditpro.ui.dialogs.audit_adjustment_dialog import AuditAdjustmentDialog
    from finauditpro.ui.dialogs.create_aje_dialog import CreateAJEDialog
    from finauditpro.ui.dialogs.lead_schedule_trace_dialog import LeadScheduleTraceDialog

    eng_svc = EngagementService(db_manager)
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    firm = firm_svc.create_firm(CreateFirmDTO(name="Dialog Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Dialog Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    map_svc = AccountMappingService(db_manager)
    adj_svc = AuditAdjustmentService(db_manager)

    # 1. Test AccountMappingDialog
    map_dlg = AccountMappingDialog(map_svc, eng.id)
    assert map_dlg.windowTitle().startswith("Schedule III")
    assert map_dlg.table.columnCount() == 8

    # 2. Test CreateAJEDialog
    create_dlg = CreateAJEDialog(adj_svc, eng.id, available_accounts=[{"account_code": "1001", "account_name": "Cash"}])
    assert create_dlg.lines_table.rowCount() == 2
    assert create_dlg.aje_num_input.text().startswith("AJE-")

    # 3. Test AuditAdjustmentDialog
    adj_dlg = AuditAdjustmentDialog(adj_svc, eng.id)
    assert adj_dlg.tabs.count() == 3
    assert adj_dlg.aje_table.columnCount() == 8
    assert adj_dlg.tb_table.columnCount() == 8
    assert adj_dlg.ls_table.columnCount() == 6

