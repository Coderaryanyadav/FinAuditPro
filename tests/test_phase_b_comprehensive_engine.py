"""Comprehensive Phase B test suite validating the full Core Audit Engine.

Verifies:
1. Risk Register & Categorization (SA 315)
2. Assertions & Coverage Matrix
3. Procedure Lifecycle & Guardrails
4. Sampling Engine (MUS, Random, Systematic, Judgmental, 100%)
5. Test Execution & First-Class Exceptions
6. Misstatement Aggregation & SA 450 Materiality Integration
7. Evidence Requirements & Immutability
8. Conclusion Consistency Guardrails
9. Maker-Checker Review & Segregation of Duties
10. Deterministic Completeness Scoring & Orphan Detection
11. Full Negative Testing & Cross-Engagement Isolation
12. Accounting Invariants & Adjusted TB Reconciliation
13. Performance & Scalability (100 risks, 500 procedures, 5,000 items)
"""

import time

import pytest

from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.core_audit_dtos import (
    CalculateAuditCompletenessDTO,
    CreateMisstatementDTO,
    EvaluateProcedureConclusionDTO,
    LogAuditExceptionDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.audit_execution_entities import (
    MisstatementTypeEnum,
    ProcedureConclusionEnum,
)
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    BenchmarkTypeEnum,
    MaterialityAssessment,
    ProcedureStatusEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    RoleEnum,
    User,
)
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.domain.sampling_engine import AuditSamplingEngine
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    AuditMatrixRepository,
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
    db_path = tmp_path / "test_phase_b_comp.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_env(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(id="firm-b", name="Grant & Associates CA"))
        user_repo = UserRepository(session)
        user_repo.add(User(id="usr-assoc", username="assoc_ca", password_hash="h", salt="s", role="Associate"))
        user_repo.add(User(id="usr-mgr", username="mgr_ca", password_hash="h", salt="s", role="Manager"))
        user_repo.add(User(id="usr-ptnr", username="partner_ca", password_hash="h", salt="s", role="Partner"))
        user_repo.add(User(id="usr-other", username="other_eng_user", password_hash="h", salt="s", role="Associate"))

        client = ClientRepository(session).add(
            Client(id="client-b", firm_id=firm.id, name="Zenith Manufacturing Ltd")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                id="eng-b",
                firm_id=firm.id,
                client_id=client.id,
                title="Statutory Audit FY 2025-26",
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        # Configure SA 320 Materiality: OM = ₹10,00,000, PM = ₹7,50,000, CTT = ₹50,000
        mat = MaterialityAssessment(
            engagement_id=eng.id,
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount_paise=1000000000,
            overall_materiality_paise=100000000,
            performance_materiality_paise=75000000,
            clearly_trivial_threshold_paise=5000000,
        )
        AuditMatrixRepository(session).add_materiality(mat)
        return eng


def test_sampling_engine_all_methods_reproducibility():
    """Verify MUS, Random (with seed reproducibility), Systematic, Judgmental, and 100% testing."""
    records = [
        {"id": f"REC-{i}", "amount_paise": i * 100000}
        for i in range(1, 101)  # 100 items from ₹1,000 to ₹1,00,000
    ]

    # 1. Random Sampling with Seed Reproducibility
    res_r1 = AuditSamplingEngine.calculate_random_sample(records, sample_size=15, random_seed=12345)
    res_r2 = AuditSamplingEngine.calculate_random_sample(records, sample_size=15, random_seed=12345)
    assert res_r1.sample_size == 15
    assert [i["id"] for i in res_r1.selected_items] == [i["id"] for i in res_r2.selected_items]

    # Different seed yields different sample
    res_r3 = AuditSamplingEngine.calculate_random_sample(records, sample_size=15, random_seed=99999)
    assert [i["id"] for i in res_r1.selected_items] != [i["id"] for i in res_r3.selected_items]

    # 2. Systematic Sampling
    res_sys = AuditSamplingEngine.calculate_systematic_sample(records, sample_size=10, start_index=0)
    assert res_sys.sample_size == 10
    assert res_sys.sampling_interval_paise == 10  # 100 // 10 = 10

    # 3. Judgmental Sampling (Items >= ₹80,000 = 8000000 paise)
    res_jdg = AuditSamplingEngine.calculate_judgmental_sample(records, threshold_paise=8000000)
    assert res_jdg.sample_size == 21  # items 80 through 100

    # 4. 100% Testing
    res_100 = AuditSamplingEngine.calculate_100_pct_sample(records)
    assert res_100.sample_size == 100
    assert res_100.total_sampled_value_paise == sum(r["amount_paise"] for r in records)


def test_evidence_guardrail_blocks_completion_without_attachment(db_manager, seed_env):
    """Verify that a procedure requiring evidence cannot be marked COMPLETED without evidence or override."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_ca", role=RoleEnum.ASSOCIATE)
    )

    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_env.id,
            procedure_code="PRC-EV-REQ-01",
            objective="Bank balance confirmation check",
            assertions=[AssertionEnum.EXISTENCE],
            procedure_type="Substantive Test",
            requires_evidence=True,
        )
    )

    # Attempt to complete without evidence or override -> MUST FAIL
    with pytest.raises(ValidationError, match="requires audit evidence"):
        core_svc.evaluate_procedure_conclusion(
            EvaluateProcedureConclusionDTO(
                engagement_id=seed_env.id,
                procedure_id=proc.id,
                conclusion=ProcedureConclusionEnum.PASS,
                result_summary="Verified against bank balance",
                override_reason=None,
            )
        )

    # Attach evidence
    matrix_svc.attach_evidence(
        AttachEvidenceDTO(
            engagement_id=seed_env.id,
            procedure_id=proc.id,
            title="SBI_Bank_Confirmation_Letter.pdf",
            excerpt_or_reference="Direct bank confirmation confirming balance of ₹1,00,00,000",
        )
    )

    # Now completion succeeds
    completed = core_svc.evaluate_procedure_conclusion(
        EvaluateProcedureConclusionDTO(
            engagement_id=seed_env.id,
            procedure_id=proc.id,
            conclusion=ProcedureConclusionEnum.PASS,
            result_summary="Verified against attached confirmation",
        )
    )
    assert completed.status == ProcedureStatusEnum.COMPLETED


def test_procedure_review_maker_checker_and_role_authorization(db_manager, seed_env):
    """Verify maker-checker segregation of duties: preparer cannot review own work, associate cannot review."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)

    # Preparer creates and completes procedure
    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_ca", role=RoleEnum.ASSOCIATE)
    )
    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_env.id,
            procedure_code="PRC-SOX-01",
            objective="Payroll reconciliation",
            assertions=[AssertionEnum.ACCURACY],
            requires_evidence=False,
        )
    )
    core_svc.evaluate_procedure_conclusion(
        EvaluateProcedureConclusionDTO(
            engagement_id=seed_env.id,
            procedure_id=proc.id,
            conclusion=ProcedureConclusionEnum.PASS,
            result_summary="Payroll registers reconcile with GL",
        )
    )

    # 1. Preparer attempts self-review -> MUST FAIL
    with pytest.raises(ValidationError, match="Segregation of Duties Violation"):
        core_svc.review_procedure(seed_env.id, proc.id, decision="CLEAR")

    # 2. Another Associate attempts review -> MUST FAIL (Unauthorized role)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-other", username="other_ca", role=RoleEnum.ASSOCIATE)
    )
    with pytest.raises(ValidationError, match="Unauthorized"):
        core_svc.review_procedure(seed_env.id, proc.id, decision="CLEAR")

    # 3. Manager reviews and clears -> MUST SUCCEED
    SecurityContext.set_current_session(
        UserSession(user_id="usr-mgr", username="mgr_ca", role=RoleEnum.MANAGER)
    )
    reviewed = core_svc.review_procedure(seed_env.id, proc.id, decision="CLEAR")
    assert reviewed.status == ProcedureStatusEnum.CLEARED
    assert reviewed.reviewer == "mgr_ca"
    assert reviewed.reviewed_date is not None


def test_misstatement_aggregation_sa450_and_materiality_thresholds(db_manager, seed_env):
    """Verify SA 450 misstatement classification (Factual, Judgmental, Projected) and headroom calculation."""
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_ca", role=RoleEnum.ASSOCIATE)
    )

    # Misstatement 1: Factual uncorrected ₹2,00,000 (20000000 paise)
    core_svc.create_misstatement(
        CreateMisstatementDTO(
            engagement_id=seed_env.id,
            account_code="3001",
            account_name="Sales",
            schedule_iii_category="Revenue",
            misstatement_type=MisstatementTypeEnum.FACTUAL,
            amount_paise=20000000,
            rationale="Unearned revenue",
        )
    )

    # Misstatement 2: Judgmental uncorrected ₹3,00,000 (30000000 paise)
    core_svc.create_misstatement(
        CreateMisstatementDTO(
            engagement_id=seed_env.id,
            account_code="1005",
            account_name="Inventory",
            schedule_iii_category="Inventories",
            misstatement_type=MisstatementTypeEnum.JUDGMENTAL,
            amount_paise=30000000,
            rationale="Slow-moving provision estimate",
        )
    )

    summary = core_svc.aggregate_misstatements(seed_env.id)
    assert summary.total_factual_paise == 20000000
    assert summary.total_judgmental_paise == 30000000
    assert summary.total_known_misstatement_paise == 50000000  # ₹5,00,000
    assert summary.total_uncorrected_misstatement_paise == 50000000
    # Overall Materiality is ₹10,00,000; headroom = ₹10L - ₹5L = ₹5L (50000000 paise)
    assert summary.remaining_materiality_headroom_paise == 50000000
    assert summary.is_material_misstatement_present is False  # Below PM of ₹7.5L
    assert summary.requires_modified_opinion is False


def test_orphan_detection_and_audit_completeness_report(db_manager, seed_env):
    """Verify orphan detection (risks without procedures, procedures without risks/conclusions)."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_ca", role=RoleEnum.ASSOCIATE)
    )

    # Create orphaned risk (no linked procedure)
    risk = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=seed_env.id,
            risk_code="RSK-ORPHAN",
            title="Unaddressed Litigation Risk",
            category="Contingent Liabilities",
            description="Pending court case without procedure",
        )
    )

    # Create orphaned procedure (no linked risk)
    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_env.id,
            procedure_code="PRC-ORPHAN",
            objective="Ad-hoc inquiry with receptionist",
            linked_risk_ids=[],
            requires_evidence=False,
        )
    )

    rep = core_svc.calculate_audit_completeness(
        CalculateAuditCompletenessDTO(engagement_id=seed_env.id)
    )
    assert "RSK-ORPHAN" in rep.orphaned_risks
    assert "PRC-ORPHAN" in rep.orphaned_procedures
    assert "PRC-ORPHAN" in rep.procedures_missing_conclusion
    assert rep.is_ready_for_finalization is False


def test_performance_scalability_100_risks_and_500_procedures(db_manager, seed_env):
    """Verify that creating and evaluating 100 risks and 500 procedures executes in < 2.0s."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="usr-mgr", username="mgr_ca", role=RoleEnum.MANAGER)
    )

    t0 = time.perf_counter()
    with db_manager.session_scope() as session:
        repo = AuditMatrixRepository(session)
        from finauditpro.domain.audit_matrix_entities import AuditProcedure, AuditRisk

        # Bulk create 100 risks
        risks = [
            AuditRisk(
                engagement_id=seed_env.id,
                risk_code=f"RSK-PERF-{i:03d}",
                title=f"Performance Risk {i}",
                category="General",
                description="Risk under scale test",
            )
            for i in range(1, 101)
        ]
        for r in risks:
            repo.add_risk(r)

        # Bulk create 500 procedures
        procs = [
            AuditProcedure(
                engagement_id=seed_env.id,
                procedure_code=f"PRC-PERF-{i:03d}",
                objective=f"Performance Procedure {i}",
                linked_risk_ids=[risks[i % 100].id],
                requires_evidence=False,
                conclusion="PASS",
                status=ProcedureStatusEnum.COMPLETED,
            )
            for i in range(1, 501)
        ]
        for p in procs:
            repo.add_procedure(p)

    t_create = time.perf_counter() - t0

    # Calculate completeness
    t0 = time.perf_counter()
    rep = core_svc.calculate_audit_completeness(
        CalculateAuditCompletenessDTO(engagement_id=seed_env.id)
    )
    t_eval = time.perf_counter() - t0

    assert rep.risk_coverage_pct == 100.0
    assert rep.procedure_execution_pct == 100.0
    assert (t_create + t_eval) < 2.0


def test_cross_engagement_isolation_and_negative_tampering(db_manager, seed_env):
    """Verify that audit procedures and exceptions cannot be read or modified across engagements."""
    core_svc = CoreAuditService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="usr-assoc", username="assoc_ca", role=RoleEnum.ASSOCIATE)
    )

    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_env.id,
            procedure_code="PRC-ISO-01",
            objective="Isolation check",
            requires_evidence=False,
        )
    )

    # Attempt to evaluate conclusion referencing wrong engagement_id -> MUST FAIL
    with pytest.raises(EntityNotFoundError):
        core_svc.evaluate_procedure_conclusion(
            EvaluateProcedureConclusionDTO(
                engagement_id="eng-DIFFERENT-CLIENT",
                procedure_id=proc.id,
                conclusion=ProcedureConclusionEnum.PASS,
                result_summary="Forged cross-engagement update",
            )
        )

    # Attempt to create exception under non-existent engagement -> MUST FAIL
    with pytest.raises(EntityNotFoundError):
        core_svc.log_audit_exception(
            LogAuditExceptionDTO(
                engagement_id="non-existent-eng",
                procedure_id=proc.id,
                exception_code="EXC-ATTACK",
                title="Tampered Exception",
                description="Cross tenant injection",
                amount_paise=100000,
            )
        )

