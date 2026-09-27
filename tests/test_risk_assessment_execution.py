"""Tests for Risk Assessment connected to Audit Execution, Deterministic Scoring, Procedure Generation, and Traceability."""

from pathlib import Path
import pytest

from finauditpro.application.audit_planning_dtos import CreateRiskDTO, CreateProcedureDTO, UpdateProcedureStatusDTO
from finauditpro.application.dtos import CreateEngagementDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditRisk,
    ProcedureStatusEnum,
    RiskSeverityEnum,
    derive_qualitative_romm,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import Base, FirmModel, ClientModel
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "test_risk_exec.db"
    db_manager = DatabaseManager(f"sqlite:///{db_file}")
    with db_manager.engine.begin() as conn:
        Base.metadata.create_all(conn)

    with db_manager.session_scope() as session:
        session.add(FirmModel(id="firm-icai-01", name="S. K. & Associates", registration_number="FRN-123456"))
        session.add(ClientModel(id="client-tatasteel", firm_id="firm-icai-01", name="Tata Steel Limited", pan="AAACT1234A"))
        session.add(ClientModel(id="client-infosys", firm_id="firm-icai-01", name="Infosys Limited", pan="AAACI5678B"))

    return db_manager


@pytest.fixture
def active_engagement(test_db: DatabaseManager) -> str:
    eng_service = EngagementService(test_db)
    eng = eng_service.create_engagement(
        CreateEngagementDTO(
            firm_id="firm-icai-01",
            client_id="client-tatasteel",
            engagement_name="Statutory Audit FY 2025-26",
            financial_year="2025-26",
            engagement_type="STATUTORY_AUDIT",
            partner="CA Rajesh Sharma",
            manager="CA Priya Mehta",
            team_members=["CA Rajesh Sharma", "CA Priya Mehta", "Auditor"],
        )
    )
    return eng.id


def test_deterministic_risk_scoring_matrix():
    """Test that official risk scoring (RoMM) strictly follows the deterministic 3x3 matrix (SA 315 / SA 330)."""
    # 1. Inherent = HIGH
    assert derive_qualitative_romm(RiskSeverityEnum.HIGH, RiskSeverityEnum.HIGH) == RiskSeverityEnum.HIGH
    assert derive_qualitative_romm(RiskSeverityEnum.HIGH, RiskSeverityEnum.MEDIUM) == RiskSeverityEnum.HIGH
    assert derive_qualitative_romm(RiskSeverityEnum.HIGH, RiskSeverityEnum.LOW) == RiskSeverityEnum.HIGH

    # 2. Inherent = MEDIUM
    assert derive_qualitative_romm(RiskSeverityEnum.MEDIUM, RiskSeverityEnum.HIGH) == RiskSeverityEnum.HIGH
    assert derive_qualitative_romm(RiskSeverityEnum.MEDIUM, RiskSeverityEnum.MEDIUM) == RiskSeverityEnum.MEDIUM
    assert derive_qualitative_romm(RiskSeverityEnum.MEDIUM, RiskSeverityEnum.LOW) == RiskSeverityEnum.MEDIUM

    # 3. Inherent = LOW
    assert derive_qualitative_romm(RiskSeverityEnum.LOW, RiskSeverityEnum.HIGH) == RiskSeverityEnum.HIGH
    assert derive_qualitative_romm(RiskSeverityEnum.LOW, RiskSeverityEnum.MEDIUM) == RiskSeverityEnum.MEDIUM
    assert derive_qualitative_romm(RiskSeverityEnum.LOW, RiskSeverityEnum.LOW) == RiskSeverityEnum.LOW


def test_risk_isolation_across_engagements(test_db: DatabaseManager, active_engagement: str):
    """Test that risks are strictly isolated to their owning engagement."""
    eng_service = EngagementService(test_db)
    eng2 = eng_service.create_engagement(
        CreateEngagementDTO(
            firm_id="firm-icai-01",
            client_id="client-infosys",
            engagement_name="Statutory Audit FY 2025-26 (Client 2)",
            financial_year="2025-26",
            engagement_type="STATUTORY_AUDIT",
            partner="CA Rajesh Sharma",
            manager="CA Priya Mehta",
        )
    )

    planning_service = AuditPlanningService(test_db)

    # Create risk in engagement 1
    risk1 = planning_service.create_risk(
        CreateRiskDTO(
            engagement_id=active_engagement,
            risk_code="RSK-REV-01",
            title="Revenue Recognition Risk",
            category="Revenue",
            description="Risk of improper cut-off in year-end sales invoicing.",
            assertions=[AssertionEnum.CUT_OFF, AssertionEnum.OCCURRENCE],
            inherent_risk=RiskSeverityEnum.HIGH,
            control_risk=RiskSeverityEnum.MEDIUM,
            is_significant_risk=True,
            planned_response="Perform extended cut-off testing 15 days around balance sheet date.",
        )
    )

    # List risks in engagement 1 vs engagement 2
    e1_risks = planning_service.list_risks(active_engagement)
    e2_risks = planning_service.list_risks(eng2.id)

    assert len(e1_risks) == 1
    assert e1_risks[0].id == risk1.id
    assert len(e2_risks) == 0

    # Cross-engagement generation must fail
    with pytest.raises(EntityNotFoundError):
        planning_service.generate_procedures_for_risk(eng2.id, risk1.id)


def test_relevant_assertions_and_recommended_procedures(test_db: DatabaseManager):
    """Test assertion mapping and procedure recommendations for standard financial areas."""
    planning_service = AuditPlanningService(test_db)

    # Assertions for Revenue
    rev_assertions = planning_service.get_relevant_assertions_for_area("Revenue from Operations")
    assert AssertionEnum.OCCURRENCE in rev_assertions
    assert AssertionEnum.CUT_OFF in rev_assertions

    # Assertions for Inventory
    inv_assertions = planning_service.get_relevant_assertions_for_area("Inventory")
    assert AssertionEnum.EXISTENCE in inv_assertions
    assert AssertionEnum.VALUATION in inv_assertions

    # Assertions for Debtors
    rec_assertions = planning_service.get_relevant_assertions_for_area("Trade Receivables")
    assert AssertionEnum.EXISTENCE in rec_assertions
    assert AssertionEnum.VALUATION in rec_assertions

    # Recommended procedures for Revenue
    rev_procs = planning_service.get_recommended_procedures("Revenue", risk_category="Sales Cutoff")
    assert len(rev_procs) > 0
    proc_codes = [p.code_prefix for p in rev_procs]
    assert any("CUTOFF" in c for c in proc_codes)


def test_risk_to_procedure_and_working_paper_generation(test_db: DatabaseManager, active_engagement: str):
    """Test full canonical generation: Risk -> Relevant Assertions -> Recommended Procedure -> Working Paper."""
    planning_service = AuditPlanningService(test_db)

    # 1. Identify Risk
    risk = planning_service.create_risk(
        CreateRiskDTO(
            engagement_id=active_engagement,
            risk_code="RSK-REV-CUT",
            title="Revenue Cut-off & Billing Timing Risk",
            category="Revenue",
            description="Risk that sales transactions near year end are recorded in wrong period.",
            assertions=[AssertionEnum.CUT_OFF],
            inherent_risk=RiskSeverityEnum.HIGH,
            control_risk=RiskSeverityEnum.HIGH,
            is_significant_risk=True,
            planned_response="Substantive cut-off testing on dispatch notes and invoices.",
        )
    )

    # Verify risk fields & properties
    assert risk.overall_risk == RiskSeverityEnum.HIGH
    assert risk.rationale == "Substantive cut-off testing on dispatch notes and invoices."
    assert risk.assertion == AssertionEnum.CUT_OFF

    # 2. Generate procedures & working papers
    generated_procs = planning_service.generate_procedures_for_risk(
        engagement_id=active_engagement,
        risk_id=risk.id,
        selected_templates=["PROC-REV-CUTOFF"],
        preparer="CA Senior Auditor",
    )

    assert len(generated_procs) == 1
    proc = generated_procs[0]

    # Verify procedure attributes
    assert proc.engagement_id == active_engagement
    assert proc.procedure_code == "PROC-REV-CUTOFF-RSK-REV-CUT"
    assert "sales invoices" in proc.objective and "accounting period" in proc.objective
    assert AssertionEnum.CUT_OFF in proc.assertions
    assert proc.linked_risk_ids == [risk.id]
    assert "e-Way Bills" in proc.evidence_requirement
    assert proc.population != ""

    # 3. Traceability navigation (Risk <-> Procedure <-> Working Paper)
    trace_service = TraceabilityService(test_db)
    risk_procs = trace_service.get_procedures_for_risk(active_engagement, risk.id)
    assert any(p.id == proc.id for p in risk_procs)

    proc_risks = trace_service.get_risks_for_procedure(active_engagement, proc.id)
    assert any(r.id == risk.id for r in proc_risks)

    proc_wps = trace_service.get_working_papers_for_procedure(active_engagement, proc.id)
    assert len(proc_wps) == 1
    wp = proc_wps[0]
    assert "Revenue Cut-off" in wp.title
    assert wp.area == risk.financial_statement_area

    risk_wps = trace_service.get_working_papers_for_risk(active_engagement, risk.id)
    assert any(w.id == wp.id for w in risk_wps)


def test_audit_trail_for_risk_and_procedure_lifecycle(test_db: DatabaseManager, active_engagement: str):
    """Test that every risk creation, procedure generation, and status change logs immutable audit events."""
    planning_service = AuditPlanningService(test_db)

    # 1. Create Risk
    risk = planning_service.create_risk(
        CreateRiskDTO(
            engagement_id=active_engagement,
            risk_code="RSK-INV-01",
            title="Inventory NRV Valuation Risk",
            category="Inventory",
            description="Risk of slow moving items carried above net realizable value.",
            assertions=[AssertionEnum.VALUATION],
            inherent_risk=RiskSeverityEnum.MEDIUM,
            control_risk=RiskSeverityEnum.HIGH,
            is_significant_risk=False,
            planned_response="Test cost vs NRV for slow moving stock.",
        )
    )

    # 2. Generate procedure
    procs = planning_service.generate_procedures_for_risk(
        engagement_id=active_engagement,
        risk_id=risk.id,
        selected_templates=["PROC-INV-COUNT"],
        preparer="CA Senior Auditor",
    )
    proc = procs[0]

    # 3. Update procedure status
    planning_service.update_procedure_status(
        UpdateProcedureStatusDTO(
            procedure_id=proc.id,
            status=ProcedureStatusEnum.COMPLETED,
            result_summary="Count sheets reconciled with zero material discrepancy.",
            conclusion="Inventory valuation is fairly stated in accordance with AS 2 / Ind AS 2.",
            reviewer="CA Priya Mehta",
        )
    )

    # 4. Verify audit trail in DB
    with test_db.session_scope() as session:
        events = AuditEventRepository(session).list_for_engagement(active_engagement)

    actions = [e.action for e in events]
    assert "RISK_CREATED" in actions
    assert "PROCEDURE_GENERATED_FROM_RISK" in actions
    assert "PROCEDURE_STATUS_UPDATED" in actions
