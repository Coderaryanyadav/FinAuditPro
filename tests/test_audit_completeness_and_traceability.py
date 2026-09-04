"""Tests for Audit Completeness Scoring, Orphan Detection, and 2-Way Traceability Graph."""

import pytest

from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.core_audit_dtos import (
    CalculateAuditCompletenessDTO,
    CreateMisstatementDTO,
    LinkMisstatementToAJEDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.domain.audit_execution_entities import (
    MisstatementTypeEnum,
)
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    RoleEnum,
    User,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture(autouse=True)
def clean_security_context():
    SecurityContext.clear()
    yield
    SecurityContext.clear()


@pytest.fixture
def db_manager(tmp_path):
    db_path = tmp_path / "test_completeness_engine.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(id="firm-1", name="CA Audit Firm"))
        user_repo = UserRepository(session)
        user_repo.add(
            User(id="user-auditor", username="auditor1", password_hash="h", salt="s", role="Senior")
        )
        client = ClientRepository(session).add(
            Client(id="client-1", firm_id=firm.id, name="ABC Manufacturing Pvt Ltd")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                id="eng-1",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        return eng


def test_orphan_detection_and_deterministic_completeness_score(db_manager, seed_engagement):
    """Verify orphan detection flags disconnected audit items and calculates a deterministic score."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    # 1. Create Risk with NO procedure (Orphaned Risk)
    risk_orphan = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=seed_engagement.id,
            risk_code="RSK-ORPHAN-001",
            title="Unhedged Foreign Exchange Exposure",
            category="Finance Costs",
            description="Forex fluctuation on USD import buyer's credit",
            assertions=[AssertionEnum.VALUATION],
        )
    )

    # 2. Create Procedure with NO risk (Orphaned Procedure) and NO conclusion
    proc_orphan = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_engagement.id,
            procedure_code="PRC-ORPHAN-002",
            objective="General review of board minutes",
            assertions=[AssertionEnum.COMPLETENESS],
            procedure_type="Inquiry",
        )
    )

    # Compute Completeness
    report = core_svc.calculate_audit_completeness(
        CalculateAuditCompletenessDTO(engagement_id=seed_engagement.id)
    )
    assert "RSK-ORPHAN-001" in report.orphaned_risks
    assert "PRC-ORPHAN-002" in report.orphaned_procedures
    assert "PRC-ORPHAN-002" in report.procedures_missing_conclusion
    assert report.is_ready_for_finalization is False
    assert report.composite_completeness_score < 95.0


def test_full_chain_2way_traceability_graph(db_manager, seed_engagement):
    """Verify bi-directional 2-way graph traversal connects Risk -> Procedure -> Finding -> Misstatement -> AJE."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    trace_svc = TraceabilityService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    # 1. Risk
    risk = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=seed_engagement.id,
            risk_code="RSK-DEBT-001",
            title="Doubtful Debts Underprovisioning",
            category="Trade Receivables",
            description="Risk that aged receivables over 180 days are unprovided",
            assertions=[AssertionEnum.VALUATION],
        )
    )

    # 2. Procedure
    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_engagement.id,
            linked_risk_ids=[risk.id],
            procedure_code="PRC-DEBT-001",
            objective="Inspect debtors aging report and sample balances > 180 days",
            assertions=[AssertionEnum.VALUATION],
            procedure_type="Substantive Test",
        )
    )

    # 3. Evidence
    ev = matrix_svc.attach_evidence(
        AttachEvidenceDTO(
            engagement_id=seed_engagement.id,
            procedure_id=proc.id,
            title="Debtors_Aging_March2026.pdf",
            excerpt_or_reference="Aging bucket >180 days contains disputed customer invoices of ₹3,00,000",
        )
    )

    # 4. Finding / Exception
    finding = matrix_svc.create_finding(
        CreateFindingDTO(
            engagement_id=seed_engagement.id,
            procedure_id=proc.id,
            risk_id=risk.id,
            title="Unprovided Doubtful Debt ₹3,00,000",
            description="Customer in liquidation; no provision recorded in books",
            category="Substantive Exception",
            severity=RiskSeverityEnum.HIGH,
            assertion=AssertionEnum.VALUATION,
            affected_account="1020",
        )
    )

    # 5. Misstatement
    misst = core_svc.create_misstatement(
        CreateMisstatementDTO(
            engagement_id=seed_engagement.id,
            exception_id=finding.id,
            procedure_id=proc.id,
            account_code="1020",
            account_name="Trade Receivables",
            schedule_iii_category="Trade Receivables",
            misstatement_type=MisstatementTypeEnum.FACTUAL,
            amount_paise=30000000,  # ₹3,00,000
            rationale="Unprovided bad debt",
        )
    )

    # 6. Link Misstatement to AJE
    core_svc.link_misstatement_to_aje(
        LinkMisstatementToAJEDTO(
            engagement_id=seed_engagement.id,
            misstatement_id=misst.id,
            aje_id="aje-uuid-1",
            aje_number="AJE-BAD-001",
        )
    )

    # 7. Traverse Traceability Graph
    graph = trace_svc.build_finding_traceability(seed_engagement.id, finding.id)
    node_types = {n["type"] for n in graph.nodes}
    assert "Finding" in node_types
    assert "Procedure" in node_types
    assert "Risk" in node_types
    assert "Misstatement" in node_types
    assert "AJE" in node_types

    edge_relations = {e["relation"] for e in graph.edges}
    assert "RAISED_BY_PROCEDURE" in edge_relations
    assert "LINKED_TO_RISK" in edge_relations
    assert "QUANTIFIED_AS_MISSTATEMENT" in edge_relations
    assert "CORRECTED_BY_AJE" in edge_relations
