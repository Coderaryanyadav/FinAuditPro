"""Tests for Audit Exception Engine, SA 450 Misstatement Aggregator, and AJE Integration."""

import pytest

from finauditpro.application.audit_adjustment_dtos import CreateAJEDTO, CreateAJELineDTO
from finauditpro.application.audit_matrix_dtos import CreateProcedureDTO
from finauditpro.application.core_audit_dtos import (
    CreateMisstatementDTO,
    LinkMisstatementToAJEDTO,
    LogAuditExceptionDTO,
    ResolveAuditExceptionDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.audit_execution_entities import (
    ExceptionStatusEnum,
    MisstatementStatusEnum,
    MisstatementTypeEnum,
)
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    BenchmarkTypeEnum,
    MaterialityAssessment,
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
    db_path = tmp_path / "test_exception_engine.db"
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

        # Set up SA 320 Materiality: Overall = ₹10,00,000, Performance = ₹7,50,000, Clearly Trivial = ₹50,000
        mat = MaterialityAssessment(
            engagement_id=eng.id,
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount_paise=1000000000,  # ₹1 Crore
            overall_materiality_paise=100000000,  # ₹10,00,000
            performance_materiality_paise=75000000,  # ₹7,50,000
            clearly_trivial_threshold_paise=5000000,  # ₹50,000
        )
        AuditMatrixRepository(session).add_materiality(mat)
        return eng


def test_exception_lifecycle_and_resolution(db_manager, seed_engagement):
    """Verify first-class exception creation, investigation, and resolution."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_engagement.id,
            procedure_code="PRC-BANK-001",
            objective="Verification of unpresented cheques in Bank Reconciliation Statement",
            assertions=[AssertionEnum.COMPLETENESS],
            procedure_type="Substantive Test",
        )
    )

    # 1. Log Exception
    exc = core_svc.log_audit_exception(
        LogAuditExceptionDTO(
            engagement_id=seed_engagement.id,
            procedure_id=proc.id,
            exception_code="EXC-BRS-001",
            title="Stale Cheques > 90 Days Unreversed in BRS",
            description="Cheques issued in October 2025 totalling ₹1,20,000 remained unpresented and unreversed",
            amount_paise=12000000,  # ₹1,20,000
            root_cause="Accounts payable clerk missed quarterly stale cheque review",
        )
    )
    assert exc.status == ExceptionStatusEnum.OPEN
    assert exc.amount_paise == 12000000

    # 2. Resolve Exception with Management Action
    resolved = core_svc.resolve_audit_exception(
        ResolveAuditExceptionDTO(
            engagement_id=seed_engagement.id,
            exception_id=exc.id,
            management_response="Management agreed and credited back stale cheques to bank balance in April",
            resolution="Auditor verified reversal journal in subsequent period bank ledger",
            is_resolved=True,
            status=ExceptionStatusEnum.RESOLVED,
        )
    )
    assert resolved.is_resolved is True
    assert resolved.status == ExceptionStatusEnum.RESOLVED


def test_misstatement_aggregation_and_aje_reconciliation(db_manager, seed_engagement):
    """Verify SA 450 misstatement aggregation against materiality and linking to AJE."""
    core_svc = CoreAuditService(db_manager)
    adj_svc = AuditAdjustmentService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    # 1. Create Factual Misstatement (Unrecorded Expense: ₹2,00,000)
    misst_1 = core_svc.create_misstatement(
        CreateMisstatementDTO(
            engagement_id=seed_engagement.id,
            account_code="4050",
            account_name="Freight Expense",
            schedule_iii_category="Other Expenses",
            misstatement_type=MisstatementTypeEnum.FACTUAL,
            amount_paise=20000000,  # ₹2,00,000
            rationale="Unaccrued inward freight bill for March 2026",
        )
    )

    # 2. Create Projected Misstatement (Inventory Valuation: ₹1,50,000)
    misst_2 = core_svc.create_misstatement(
        CreateMisstatementDTO(
            engagement_id=seed_engagement.id,
            account_code="1020",
            account_name="Raw Material Stock",
            schedule_iii_category="Inventories",
            misstatement_type=MisstatementTypeEnum.PROJECTED,
            amount_paise=15000000,  # ₹1,50,000
            rationale="Statistical projection of obsolete chemical stock valuation error",
        )
    )

    # Check Initial SA 450 Aggregation
    agg_initial = core_svc.aggregate_misstatements(seed_engagement.id)
    assert agg_initial.total_factual_paise == 20000000
    assert agg_initial.total_projected_paise == 15000000
    assert agg_initial.total_uncorrected_misstatement_paise == 35000000  # ₹3,50,000
    assert (
        agg_initial.remaining_materiality_headroom_paise == 65000000
    )  # ₹10,00,000 - ₹3,50,000 = ₹6,50,000
    assert (
        agg_initial.is_material_misstatement_present is False
    )  # Below ₹7.5L performance materiality

    # 3. Create Balanced AJE for Misstatement 1 (Dr Freight ₹2,00,000, Cr Creditors ₹2,00,000)
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=seed_engagement.id,
            aje_number="AJE-FRT-001",
            entry_date="2026-03-31",
            title="Freight Accrual",
            narration="Accrue unrecorded freight for March",
            reason="Correct Misstatement MISST-1",
            lines=[
                CreateAJELineDTO(
                    account_code="4050",
                    account_name="Freight Expense",
                    debit_paise=20000000,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="2020",
                    account_name="Trade Creditors",
                    debit_paise=0,
                    credit_paise=20000000,
                ),
            ],
        )
    )

    # 4. Link Misstatement to AJE
    corrected_misst = core_svc.link_misstatement_to_aje(
        LinkMisstatementToAJEDTO(
            engagement_id=seed_engagement.id,
            misstatement_id=misst_1.id,
            aje_id=aje.id,
            aje_number=aje.aje_number,
        )
    )
    assert corrected_misst.is_corrected is True
    assert corrected_misst.status == MisstatementStatusEnum.CORRECTED

    # Check Updated SA 450 Aggregation
    agg_after = core_svc.aggregate_misstatements(seed_engagement.id)
    assert agg_after.total_corrected_misstatement_paise == 20000000
    assert (
        agg_after.total_uncorrected_misstatement_paise == 15000000
    )  # Only ₹1.5L remains uncorrected
    assert agg_after.remaining_materiality_headroom_paise == 85000000  # ₹8,50,000
