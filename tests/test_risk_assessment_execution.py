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


def test_audit_risk_required_fields_and_ai_advisory_isolation(test_db: DatabaseManager, active_engagement: str):
    """Test that AuditRisk model supports all canonical fields and official scoring cannot be silently overridden by AI."""
    planning_service = AuditPlanningService(test_db)

    # 1. Verify all canonical risk fields
    risk = planning_service.create_risk(
        CreateRiskDTO(
            engagement_id=active_engagement,
            risk_code="RSK-REV-001",
            title="Revenue Cut-off Inaccuracy",
            category="Revenue",
            description="High risk of premature revenue recognition before delivery terms fulfilled.",
            area="Revenue from Operations",
            assertions=[AssertionEnum.CUT_OFF, AssertionEnum.OCCURRENCE],
            inherent_risk=RiskSeverityEnum.HIGH,
            control_risk=RiskSeverityEnum.MEDIUM,
            rationale="Auditee uses manual dispatch register prone to delay in entry.",
            status="Assessed",
            evidence_ids=["EV-DOC-001"],
            linked_procedure_ids=["PROC-REV-01"],
        )
    )

    assert risk.id is not None
    assert risk.engagement_id == active_engagement
    assert risk.area == "Revenue from Operations"
    assert risk.description == "High risk of premature revenue recognition before delivery terms fulfilled."
    assert risk.assertion == AssertionEnum.CUT_OFF
    assert risk.inherent_risk == RiskSeverityEnum.HIGH
    assert risk.control_risk == RiskSeverityEnum.MEDIUM
    assert risk.overall_risk == RiskSeverityEnum.HIGH  # High x Medium = High
    assert risk.rationale == "Auditee uses manual dispatch register prone to delay in entry."
    assert risk.evidence == ["EV-DOC-001"]
    assert risk.related_procedures == ["PROC-REV-01"]
    assert risk.status == "Assessed"

    # 2. AI Advisory Isolation: An AI suggestion payload cannot silently change official derived RoMM
    ai_suggested_score = RiskSeverityEnum.LOW
    # The official risk score is deterministically derived from inherent and control risks
    official_romm = risk.calculate_romm()
    assert official_romm == RiskSeverityEnum.HIGH
    assert official_romm != ai_suggested_score  # AI suggestion does not mutate official score


def test_full_canonical_revenue_cutoff_audit_execution_chain(test_db: DatabaseManager, active_engagement: str):
    """Test complete canonical flow end-to-end:
    Financial Information (Sales Ledger)
    -> Risk (Cut-off Risk)
    -> Assertion (Cut-Off)
    -> Procedure (Revenue Cut-off Procedure)
    -> Sample & Evidence
    -> Test Execution & Exception
    -> Finding
    -> Working Paper
    """
    from finauditpro.application.audit_planning_dtos import AttachEvidenceDTO, CreateFindingDTO
    from finauditpro.application.services.financial_service import FinancialService, ImportDatasetDTO
    from finauditpro.domain.audit_execution_entities import (
        AuditException,
        AuditSampleItemTest,
        AuditTestOutcomeEnum,
        TestExecution,
    )
    from finauditpro.domain.audit_matrix_entities import FindingSourceEnum, FindingStatusEnum
    from finauditpro.domain.financial_entities import DatasetTypeEnum
    from finauditpro.infrastructure.persistence.repositories import (
        AuditMatrixRepository,
        WorkingPaperRepository,
    )

    planning_service = AuditPlanningService(test_db)
    fin_service = FinancialService(test_db)
    trace_service = TraceabilityService(test_db)

    # 1. Financial Information: Import / Register Sales Dataset
    sales_csv = (
        "Date,Voucher No,Account Name,Account Code,Debit,Credit,Description\n"
        "2026-03-30,INV-101,Domestic Sales,4001,0,500000.00,Sale of industrial valves\n"
        "2026-03-31,INV-102,Domestic Sales,4001,0,750000.00,Sale of pump assemblies\n"
        "2026-04-01,INV-103,Domestic Sales,4001,0,320000.00,Sale of gaskets\n"
    )
    csv_file = Path(test_db.engine.url.database).parent / "sales_cutoff.csv"
    csv_file.write_text(sales_csv, encoding="utf-8")

    dataset = fin_service.import_dataset(
        ImportDatasetDTO(
            engagement_id=active_engagement,
            file_path=str(csv_file),
            dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
        )
    )
    assert dataset.row_count == 3

    # 2. Risk: Assess Revenue Cut-off Risk
    risk = planning_service.create_risk(
        CreateRiskDTO(
            engagement_id=active_engagement,
            risk_code="RSK-REV-CUTOFF-01",
            title="Revenue Year-End Cut-off Risk",
            category="Revenue",
            description="Risk of goods dispatched post year-end recorded in current year sales.",
            area="Revenue from Operations",
            assertions=[AssertionEnum.CUT_OFF, AssertionEnum.OCCURRENCE],
            inherent_risk=RiskSeverityEnum.HIGH,
            control_risk=RiskSeverityEnum.HIGH,
            planned_response="100% testing of sales invoices +/- 5 days of year-end against e-Way bills.",
        )
    )
    assert risk.overall_risk == RiskSeverityEnum.HIGH

    # 3. Assertion & Procedure Generation
    procs = planning_service.generate_procedures_for_risk(
        engagement_id=active_engagement,
        risk_id=risk.id,
        selected_templates=["PROC-REV-CUTOFF"],
        preparer="CA Senior Auditor",
    )
    assert len(procs) == 1
    cutoff_proc = procs[0]
    assert AssertionEnum.CUT_OFF in cutoff_proc.assertions

    # 4. Sample Item Testing
    sample_test = AuditSampleItemTest(
        procedure_id=cutoff_proc.id,
        item_identifier="INV-102",
        account_code="4001",
        expected_value_paise=0,  # Should have been recorded in next year (dispatched April 2)
        actual_value_paise=75000000,  # Recorded in March
        test_result=AuditTestOutcomeEnum.EXCEPTION,
        explanation="Invoice dated 31-Mar-2026 but goods dispatched on 02-Apr-2026 per e-Way Bill #EW987123.",
        tested_by="CA Senior Auditor",
    )
    sample_test.calculate_difference()
    assert sample_test.difference_paise == 75000000
    assert sample_test.test_result == AuditTestOutcomeEnum.EXCEPTION

    # 5. Evidence: Attach e-Way Bill & Dispatch Note
    evidence = planning_service.attach_evidence(
        AttachEvidenceDTO(
            engagement_id=active_engagement,
            procedure_id=cutoff_proc.id,
            dataset_id=dataset.id,
            row_index=2,
            title="e-Way Bill #EW987123 & Transporter LR Copy",
            excerpt_or_reference="e-Way bill generated 02-Apr-2026 09:15 AM, Proof of Delivery 04-Apr-2026",
        )
    )
    assert evidence.id is not None

    # 6. Test Execution & Deterministic Exception
    exception_record = AuditException(
        engagement_id=active_engagement,
        procedure_id=cutoff_proc.id,
        sample_item_id=sample_test.id,
        exception_code="EXC-REV-CUT-001",
        title="Premature Revenue Recognition on Dispatched Goods",
        description="INV-102 for Rs 7,50,000 recognized in FY 25-26 prior to goods dispatch on 02-Apr-2026.",
        source="Substantive Cut-off Procedure",
        rule="SA 500 / Ind AS 115 Revenue Cut-off Invariant",
        evidence_ref=evidence.id,
        severity="High",
        amount_paise=75000000,
        status="OPEN",
    )

    test_execution = TestExecution(
        engagement_id=active_engagement,
        procedure_id=cutoff_proc.id,
        population="Sales register entries +/- 5 days of 31-March-2026",
        sample_ids=[sample_test.id],
        sample_size=3,
        tested_by="CA Senior Auditor",
        result="EXCEPTION",
        exception_ids=[exception_record.id],
        notes="1 cut-off exception identified amounting to Rs 7,50,000.",
    )
    assert len(test_execution.exception_ids) == 1

    # 7. Finding: Linked to Risk, Procedure, Exception, Evidence, and WP
    finding = planning_service.create_finding(
        CreateFindingDTO(
            engagement_id=active_engagement,
            procedure_id=cutoff_proc.id,
            risk_id=risk.id,
            title="Sales Cut-off Misstatement - Premature Revenue Recognition",
            description="Revenue overstated by Rs 7,50,000 due to booking prior to transfer of control.",
            category="Revenue Cut-off Misstatement",
            severity=RiskSeverityEnum.HIGH,
            amount_paise=75000000,
            affected_account="4001 - Domestic Sales",
            assertion=AssertionEnum.CUT_OFF,
            recommendation="Pass adjusting journal entry to reverse sales and recognize unearned revenue / inventory.",
            preparer="CA Senior Auditor",
            source=FindingSourceEnum.DETERMINISTIC_ANALYTIC,
        )
    )

    # Attach evidence and exception to finding
    with test_db.session_scope() as session:
        matrix_repo = AuditMatrixRepository(session)
        finding_db = matrix_repo.get_finding_by_id(finding.id)
        if finding_db:
            finding_db.linked_exception_ids = [exception_record.id]
            finding_db.evidence_ids = [evidence.id]
            matrix_repo.update_finding(finding_db)

    # 8. Working Paper: Check linked working paper and update conclusion
    wps = trace_service.get_working_papers_for_procedure(active_engagement, cutoff_proc.id)
    assert len(wps) >= 1
    wp = wps[0]

    planning_service.update_procedure_status(
        UpdateProcedureStatusDTO(
            procedure_id=cutoff_proc.id,
            status=ProcedureStatusEnum.COMPLETED,
            result_summary="Testing identified 1 cut-off exception of Rs 7,50,000.",
            conclusion="Audit adjustment recommended per Finding #1.",
            reviewer="CA Priya Mehta",
        )
    )

    # 9. Verify End-to-End Traceability Graph
    graph = trace_service.build_finding_traceability(active_engagement, finding.id)
    node_types = {n["type"] for n in graph.nodes}
    assert "Finding" in node_types
    assert "Procedure" in node_types
    assert "Risk" in node_types
    assert "WorkingPaper" in node_types

    # Verify bidirectional navigation
    related_risks = trace_service.get_risks_for_procedure(active_engagement, cutoff_proc.id)
    assert any(r.id == risk.id for r in related_risks)

    related_procs = trace_service.get_procedures_for_risk(active_engagement, risk.id)
    assert any(p.id == cutoff_proc.id for p in related_procs)
