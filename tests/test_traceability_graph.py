"""Tests for 2-Way Audit Traceability Graph Navigation."""

import pytest

from finauditpro.application.audit_planning_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_traceability(tmp_path):
    db_file = tmp_path / "test_traceability.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    planning_svc = AuditPlanningService(db_manager)
    traceability_svc = TraceabilityService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Traceability Firm", firm_registration_number="FRN-888888"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Traceability Enterprise", gstin="27AAACU9603R1ZN"))
    eng = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26", lead_auditor="Lead Auditor"))

    return eng, planning_svc, traceability_svc


def test_two_way_traceability_graph_navigation(setup_traceability) -> None:
    """Verify Finding -> Procedure -> Risk -> Assertion and Finding -> Evidence graph resolution."""
    eng, planning_svc, traceability_svc = setup_traceability

    # 1. Create Risk
    risk = planning_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-REV-01",
            title="Unrecorded Revenue",
            category="Revenue Recognition",
            description="Cut-off misstatement.",
            assertions=[AssertionEnum.COMPLETENESS, AssertionEnum.CUT_OFF],
            inherent_risk=RiskSeverityEnum.HIGH,
            control_risk=RiskSeverityEnum.MEDIUM,
        )
    )

    # 2. Create Procedure linked to Risk
    proc = planning_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            procedure_code="PROC-REV-01",
            objective="Sample testing sales invoices.",
            linked_risk_ids=[risk.id],
            assertions=[AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY],
        )
    )

    # 3. Create Finding linked to Procedure
    finding = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            procedure_id=proc.id,
            risk_id=risk.id,
            title="Invoice #1005 Revenue Cut-Off Exception",
            description="Dated FY27 posted in FY26.",
            severity=RiskSeverityEnum.HIGH,
            amount_paise=100000000,
        )
    )

    # 4. Attach Evidence
    planning_svc.attach_evidence(
        AttachEvidenceDTO(
            engagement_id=eng.id,
            finding_id=finding.id,
            procedure_id=proc.id,
            document_id=None,
            page_number=3,
            title="Invoice 1005 Page 3",
            excerpt_or_reference="Dated 02-Apr-2026",
        )
    )

    # 5. Build Traceability Graph
    graph = traceability_svc.build_finding_traceability(eng.id, finding.id)

    node_types = {n["type"] for n in graph.nodes}
    assert "Finding" in node_types
    assert "Procedure" in node_types
    assert "Risk" in node_types
    assert "Assertion" in node_types
    assert "DocumentPage" in node_types

    edge_relations = {e["relation"] for e in graph.edges}
    assert "HAS_EVIDENCE" in edge_relations
    assert "RAISED_BY_PROCEDURE" in edge_relations
    assert "RESPONDS_TO_RISK" in edge_relations
