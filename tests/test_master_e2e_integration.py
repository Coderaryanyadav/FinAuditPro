"""Master full-chain integration test asserting end-to-end audit workflow and traceability resolution."""

import csv

import pytest

from finauditpro.application.audit_planning_dtos import (
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.financial_dtos import ImportDatasetDTO
from finauditpro.application.report_dtos import ApproveReportDTO, ExportReportDTO, GenerateReportDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.domain.financial_entities import DatasetTypeEnum
from finauditpro.domain.report_entities import ExportFormatEnum
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository


@pytest.fixture
def setup_master_env(tmp_path):
    db_file = tmp_path / "test_master_e2e.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Master Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Master Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    fin_svc = FinancialDataService(db_manager)
    planning_svc = AuditPlanningService(db_manager)
    wp_svc = WorkingPaperService(db_manager)
    report_svc = ReportService(db_manager)
    trace_svc = TraceabilityService(db_manager)

    return eng, fin_svc, planning_svc, wp_svc, report_svc, trace_svc, db_manager, tmp_path


def test_master_full_chain_integration_and_traceability(setup_master_env) -> None:
    """Master full-chain test: Firm -> Client -> Engagement -> Import -> Risk -> Procedure -> Finding -> WorkingPaper -> Report -> Approval -> Hash Traceability."""
    eng, fin_svc, planning_svc, wp_svc, report_svc, trace_svc, db_manager, tmp_path = setup_master_env

    # 1. Financial Import via CSV
    csv_file = tmp_path / "master_gl.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Voucher Type", "Voucher No", "Account Code", "Account Name", "Debit", "Credit", "Narration"])
        writer.writerow(["2025-10-01", "Payment", "VCH-001", "5001", "Legal Fees", 500000.0, 0.0, "Legal consultation fee"])

    ds = fin_svc.import_financial_dataset(
        ImportDatasetDTO(
            engagement_id=eng.id,
            dataset_name="Master GL",
            dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
            file_path=str(csv_file),
        )
    )
    assert ds.id is not None

    # 2. Risk & Procedure
    risk = planning_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-MASTER-01",
            title="Unrecorded Expense Risk",
            category="Purchases",
            description="Completeness misstatement.",
            assertions=[AssertionEnum.COMPLETENESS],
            inherent_risk=RiskSeverityEnum.HIGH,
        )
    )

    proc = planning_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            procedure_code="PROC-MASTER-01",
            objective="Voucher sampling testing.",
            linked_risk_ids=[risk.id],
            assertions=[AssertionEnum.COMPLETENESS],
        )
    )

    # 3. Finding
    finding = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            procedure_id=proc.id,
            risk_id=risk.id,
            title="Unrecorded Legal Invoice Exception",
            description="Voucher VCH-001 legal fee exception.",
            severity=RiskSeverityEnum.HIGH,
            amount_paise=50000000,
        )
    )

    # 4. Working Paper
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-MASTER-01",
            title="Legal Expenses Substantive Testing",
            area="Expenses",
            preparer_id="Senior Auditor",
            procedure_ids=[proc.id],
        )
    )

    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Audit Partner",
            user_role="Partner",
        )
    )

    # 5. Report Generation & Approval
    tpls = report_svc.list_templates()
    report = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng.id,
            template_id=tpls[0].id,
            title="Master Engagement Final Report",
            generated_by="Senior Auditor",
        )
    )

    approved = report_svc.approve_report(
        ApproveReportDTO(
            report_id=report.id,
            approved_by="Audit Partner",
            approver_role="Partner",
        )
    )
    assert approved.status.value == "Approved"

    # 6. Export XLSX with formula injection escaping
    xlsx_path = report_svc.export_to_xlsx(ExportReportDTO(report_id=report.id, export_format=ExportFormatEnum.XLSX))
    assert xlsx_path.endswith(".xlsx")

    # 7. Traceability Verification
    graph = trace_svc.build_finding_traceability(eng.id, finding.id)
    node_types = {n["type"] for n in graph.nodes}
    assert "Finding" in node_types
    assert "Procedure" in node_types
    assert "Risk" in node_types

    # 8. Cryptographic Audit Chain Verification
    with db_manager.session_scope() as session:
        audit_repo = AuditEventRepository(session)
        assert audit_repo.verify_chain() is True
