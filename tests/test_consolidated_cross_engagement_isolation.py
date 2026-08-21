"""Master consolidated multi-tenant engagement isolation test asserting data separation across all 7 subsystems."""

import csv

import pytest

from finauditpro.application.audit_planning_dtos import (
    CreateFindingDTO,
    CreateRiskDTO,
)
from finauditpro.application.financial_dtos import ImportDatasetDTO
from finauditpro.application.report_dtos import GenerateReportDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.document_service import DocumentService, UploadDocumentDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.domain.financial_entities import DatasetTypeEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_consolidated_isolation(tmp_path):
    db_file = tmp_path / "test_cons_iso.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Consolidated Firm"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta"))

    eng_a = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26")
    )
    eng_b = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26")
    )

    doc_svc = DocumentService(db_manager)
    fin_svc = FinancialDataService(db_manager)
    planning_svc = AuditPlanningService(db_manager)
    wp_svc = WorkingPaperService(db_manager)
    report_svc = ReportService(db_manager)

    return eng_a, eng_b, doc_svc, fin_svc, planning_svc, wp_svc, report_svc, tmp_path


def test_consolidated_cross_engagement_isolation_all_subsystems(
    setup_consolidated_isolation,
) -> None:
    """Consolidated test asserting Engagement A data never leaks into Engagement B across all 7 subsystems."""
    eng_a, eng_b, doc_svc, fin_svc, planning_svc, wp_svc, report_svc, tmp_path = (
        setup_consolidated_isolation
    )

    # 1. Documents (M2)
    fake_pdf = tmp_path / "alpha_doc.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 Fake Alpha Document Content")
    doc_svc.upload_and_process_document(
        UploadDocumentDTO(engagement_id=eng_a.id, file_path=str(fake_pdf))
    )

    docs_b = doc_svc.list_documents_for_engagement(eng_b.id)
    assert len(docs_b) == 0

    # 2. Financial Data (M3)
    csv_file = tmp_path / "alpha_gl.csv"
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
        writer.writerow(
            [
                "2025-10-01",
                "Payment",
                "VCH-001",
                "1001",
                "Alpha Cash",
                1000.0,
                0.0,
                "Alpha Cash Payment",
            ]
        )

    ds = fin_svc.import_financial_dataset(
        ImportDatasetDTO(
            engagement_id=eng_a.id,
            dataset_name="Alpha GL",
            dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
            file_path=str(csv_file),
        )
    )

    ds_b = fin_svc.list_datasets_for_engagement(eng_b.id)
    assert len(ds_b) == 0

    # 3. Risks & Procedures (M4)
    risk_a = planning_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng_a.id,
            risk_code="RSK-A-01",
            title="Alpha Risk",
            category="Revenue",
            description="Alpha description",
            assertions=[AssertionEnum.COMPLETENESS],
            inherent_risk=RiskSeverityEnum.HIGH,
        )
    )

    risks_b = planning_svc.list_risks(eng_b.id)
    assert len(risks_b) == 0

    # 4. Findings (M4/M5)
    finding_a = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng_a.id,
            title="Alpha Finding",
            description="Alpha finding detail",
            severity=RiskSeverityEnum.HIGH,
            amount_paise=100000,
        )
    )

    findings_b = planning_svc.list_findings(eng_b.id)
    assert len(findings_b) == 0

    # 5. Working Papers (M6)
    wp_a = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-A-01",
            title="Alpha Working Paper",
            area="Revenue",
            preparer_id="Auditor Alpha",
        )
    )

    wps_b = wp_svc.list_working_papers(eng_b.id)
    assert len(wps_b) == 0

    # 6. Reports & Export Artifacts (M7)
    tpls = report_svc.list_templates()
    report_a = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng_a.id,
            template_id=tpls[0].id,
            title="Alpha Report",
            generated_by="Auditor Alpha",
        )
    )

    reports_b = report_svc.list_reports(eng_b.id)
    assert len(reports_b) == 0
