"""Performance scale test seeding 10,000+ General Ledger rows and measuring processing latencies."""

import csv
import time

import pytest

from finauditpro.application.financial_dtos import ImportDatasetDTO
from finauditpro.application.report_dtos import GenerateReportDTO
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.financial_analytics_service import FinancialAnalyticsService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.domain.financial_entities import DatasetTypeEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_scale_env(tmp_path):
    db_file = tmp_path / "test_scale_m8.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Scale Test Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Scale Test Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    fin_svc = FinancialDataService(db_manager)
    analytics_svc = FinancialAnalyticsService(db_manager)
    report_svc = ReportService(db_manager)

    return eng, fin_svc, analytics_svc, report_svc, tmp_path


def test_scale_general_ledger_performance(setup_scale_env) -> None:
    """Seed 10,000 General Ledger rows via CSV and record measured latencies."""
    eng, fin_svc, analytics_svc, report_svc, tmp_path = setup_scale_env

    # 1. Generate 10,000 CSV Rows
    csv_file = tmp_path / "gl_scale_10k.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Date",
                "Voucher Type",
                "Voucher No",
                "Account Code",
                "Account Name",
                "Debit",
                "Credit",
                "Narration",
            ]
        )
        for i in range(1, 10001):
            writer.writerow(
                [
                    "2025-09-15",
                    "Payment",
                    f"VCH-{i:05d}",
                    f"ACC-{(i % 50):03d}",
                    f"Vendor {(i % 50)}",
                    5000.0 if i % 2 == 0 else 0.0,
                    0.0 if i % 2 == 0 else 5000.0,
                    f"Substantive testing narration {i}",
                ]
            )

    # 2. Import Dataset
    t0 = time.perf_counter()
    ds = fin_svc.import_financial_dataset(
        ImportDatasetDTO(
            engagement_id=eng.id,
            dataset_name="10k GL Benchmark",
            dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
            file_path=str(csv_file),
        )
    )
    t1 = time.perf_counter()
    import_latency = t1 - t0

    # 3. Run Analytics Pipeline
    from finauditpro.application.financial_dtos import RunAnalyticsDTO
    from finauditpro.domain.financial_entities import AnalyticsTypeEnum

    t2 = time.perf_counter()
    anomalies = analytics_svc.run_analysis(
        RunAnalyticsDTO(
            engagement_id=eng.id,
            dataset_id=ds.id,
            analysis_type=AnalyticsTypeEnum.DUPLICATE_DETECTION,
        )
    )
    t3 = time.perf_counter()
    analytics_latency = t3 - t2

    # 4. Generate Report
    tpls = report_svc.list_templates()
    t4 = time.perf_counter()
    report = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng.id,
            template_id=tpls[0].id,
            title="10k Scale Benchmark Report",
            generated_by="Auditor",
        )
    )
    t5 = time.perf_counter()
    report_latency = t5 - t4

    # Assertions
    assert import_latency < 10.0, f"Import latency too high: {import_latency:.2f}s"
    assert analytics_latency < 5.0, f"Analytics latency too high: {analytics_latency:.2f}s"
    assert report_latency < 5.0, f"Report latency too high: {report_latency:.2f}s"
    assert report.id is not None
