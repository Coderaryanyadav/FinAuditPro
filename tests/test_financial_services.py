"""Integration tests for FinancialDataService and FinancialAnalyticsService."""

import pytest

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.financial_dtos import ImportDatasetDTO, RunAnalyticsDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_analytics_service import FinancialAnalyticsService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.financial_entities import AnalyticsTypeEnum, DatasetTypeEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def setup_services(tmp_path):
    db_path = tmp_path / "test_fin_svc.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Fin Audit Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Fin Client Inc"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    data_svc = FinancialDataService(manager)
    analytics_svc = FinancialAnalyticsService(manager)

    return manager, eng, data_svc, analytics_svc


def test_import_and_analytics_lifecycle(setup_services, tmp_path) -> None:
    _manager, eng, data_svc, analytics_svc = setup_services

    csv_file = tmp_path / "general_ledger.csv"
    csv_file.write_text(
        "Posting Date,Vch No,Account Name,Debit,Credit,Particulars\n"
        "2026-04-10,INV-1001,Consulting Expense,150000,0,Payment to Vendor A\n"
        "2026-04-10,INV-1002,Consulting Expense,150000,0,Payment to Vendor A\n"
        "2026-04-12,INV-1005,Machinery Purchase,1000000,0,Plant Equipment\n",
        encoding="utf-8",
    )

    # 1. File Inspection
    inspection = data_svc.inspect_file(csv_file)
    assert "Posting Date" in inspection.headers
    assert inspection.suggested_mappings.get("date") == "Posting Date"

    # 2. Import Dataset
    import_dto = ImportDatasetDTO(
        engagement_id=eng.id,
        dataset_name="FY 2025-26 General Ledger",
        dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
        file_path=str(csv_file),
    )
    dataset = data_svc.import_financial_dataset(import_dto)
    assert dataset.id is not None
    assert dataset.row_count == 3

    # 3. Retrieve Records
    records = data_svc.get_dataset_records(dataset.id)
    assert len(records) == 3
    assert records[0].account_name == "Consulting Expense"
    assert records[0].debit == 150000.0

    # 4. Run Duplicate Analytics
    dup_res = analytics_svc.run_analysis(
        RunAnalyticsDTO(
            engagement_id=eng.id,
            dataset_id=dataset.id,
            analysis_type=AnalyticsTypeEnum.DUPLICATE_DETECTION,
        )
    )
    assert dup_res.anomaly_count == 2

    # 5. Run High Value Analytics
    large_res = analytics_svc.run_analysis(
        RunAnalyticsDTO(
            engagement_id=eng.id,
            dataset_id=dataset.id,
            analysis_type=AnalyticsTypeEnum.HIGH_VALUE_ANOMALY,
            threshold=500000.0,
        )
    )
    assert large_res.anomaly_count == 1

    # 6. Check Flagged Anomalies List
    anomalies = analytics_svc.list_flagged_anomalies_for_engagement(eng.id)
    assert len(anomalies) == 3
