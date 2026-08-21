"""Unit tests for WorkingPaper 2-way graph traceability (WorkingPaper -> Procedure -> Risk -> Evidence -> Finding with M5 AI badge)."""

import pytest

from finauditpro.application.audit_planning_dtos import (
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_traceability_wp(tmp_path):
    db_file = tmp_path / "test_wp_trace.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Traceability Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Traceability Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    planning_svc = AuditPlanningService(db_manager)
    wp_svc = WorkingPaperService(db_manager)
    trace_svc = TraceabilityService(db_manager)

    return eng, planning_svc, wp_svc, trace_svc


def test_working_paper_traceability_graph_resolution(setup_traceability_wp) -> None:
    """Verify 2-way graph traversal: WorkingPaper -> Procedure -> Risk -> Finding."""
    eng, planning_svc, wp_svc, trace_svc = setup_traceability_wp

    # 1. Create Risk
    risk = planning_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-WP-01",
            title="Unrecorded Expenses",
            category="Purchases",
            description="Completeness misstatement.",
            assertions=[AssertionEnum.COMPLETENESS],
            inherent_risk=RiskSeverityEnum.HIGH,
        )
    )

    # 2. Create Procedure
    proc = planning_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            procedure_code="PROC-WP-01",
            objective="Inspect purchase register vouchers.",
            linked_risk_ids=[risk.id],
            assertions=[AssertionEnum.COMPLETENESS],
        )
    )

    # 3. Create AI-Assisted Finding (M5 Model)
    finding = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            procedure_id=proc.id,
            risk_id=risk.id,
            title="Unrecorded Vendor Invoice Exception",
            description="Invoice #204 unrecorded at year-end.",
            severity=RiskSeverityEnum.HIGH,
            amount_paise=5000000,
        )
    )

    # 4. Create Working Paper linking Procedure & Finding
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-PUR-001",
            title="Purchases Substantive Testing",
            area="D. Purchases & Payables",
            preparer_id="Senior Auditor",
            procedure_ids=[proc.id],
        )
    )

    # Add link to Finding
    with wp_svc.db_manager.session_scope() as session:
        from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
            WorkingPaperRepository,
        )

        repo = WorkingPaperRepository(session)
        repo.add_link("link-find-1", wp.id, "finding", finding.id)

    # 5. Build Traceability Graph
    graph = trace_svc.build_finding_traceability(eng.id, finding.id)

    node_types = {n["type"] for n in graph.nodes}
    assert "Finding" in node_types
    assert "Procedure" in node_types
    assert "Risk" in node_types
    assert "WorkingPaper" in node_types
