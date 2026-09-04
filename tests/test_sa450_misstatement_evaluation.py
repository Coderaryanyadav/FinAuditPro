"""Tests for SA 450 Misstatement Evaluation and Materiality Comparison Engine."""

from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_completion_service import AuditCompletionService
from finauditpro.domain.audit_completion_engine import AuditCompletionEngine
from finauditpro.domain.audit_completion_entities import (
    FinancialMisstatement,
    MisstatementStatusEnum,
    MisstatementTypeEnum,
    SA450AuditConclusionEnum,
)
from finauditpro.domain.audit_execution_entities import AuditMisstatement
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
    CoreAuditEngineRepository,
)


def test_sa450_pure_engine_uncorrected_below_materiality() -> None:
    misstatements = [
        FinancialMisstatement(
            engagement_id="eng-1",
            misstatement_number="MISST-001",
            misstatement_type=MisstatementTypeEnum.FACTUAL,
            status=MisstatementStatusEnum.UNCORRECTED,
            title="Prepaid Expenses unamortized",
            description="Under-amortization of insurance",
            affected_fs_area="Other Current Assets",
            amount_paise=5000000,  # ₹50,000
        ),
        FinancialMisstatement(
            engagement_id="eng-1",
            misstatement_number="MISST-002",
            misstatement_type=MisstatementTypeEnum.JUDGMENTAL,
            status=MisstatementStatusEnum.CORRECTED,
            title="Inventory valuation adjustment",
            description="NRV adjustment posted via AJE",
            affected_fs_area="Inventories",
            amount_paise=20000000,  # ₹2,00,000
        ),
    ]

    summary = AuditCompletionEngine.evaluate_sa450_misstatements(
        engagement_id="eng-1",
        misstatements=misstatements,
        overall_materiality_paise=100000000,  # ₹10,00,000
        performance_materiality_paise=75000000,
        clearly_trivial_threshold_paise=5000000,
    )

    assert summary.total_identified_misstatements == 2
    assert summary.total_corrected_misstatements == 1
    assert summary.total_uncorrected_misstatements == 1
    assert summary.total_uncorrected_amount_paise == 5000000
    assert not summary.is_material_individually
    assert not summary.is_material_in_aggregate
    assert not summary.requires_opinion_modification
    assert summary.audit_conclusion == SA450AuditConclusionEnum.UNQUALIFIED_ACCEPTABLE


def test_sa450_pure_engine_uncorrected_exceeding_materiality() -> None:
    misstatements = [
        FinancialMisstatement(
            engagement_id="eng-1",
            misstatement_number="MISST-001",
            misstatement_type=MisstatementTypeEnum.FACTUAL,
            status=MisstatementStatusEnum.UNCORRECTED,
            title="Unrecorded Revenue Cutoff",
            description="Early revenue recognition in March",
            affected_fs_area="Revenue from Operations",
            amount_paise=120000000,  # ₹12,00,000 (exceeds ₹10L OM)
        )
    ]

    summary = AuditCompletionEngine.evaluate_sa450_misstatements(
        engagement_id="eng-1",
        misstatements=misstatements,
        overall_materiality_paise=100000000,  # ₹10,00,000
        performance_materiality_paise=75000000,
        clearly_trivial_threshold_paise=5000000,
    )

    assert summary.is_material_individually
    assert summary.is_material_in_aggregate
    assert summary.requires_opinion_modification
    assert summary.audit_conclusion == SA450AuditConclusionEnum.MODIFIED_OPINION_REQUIRED


def test_sa450_service_evaluation(tmp_path: any) -> None:
    db_path = tmp_path / "test_sa450.db"
    db_manager = initialize_database(db_path)

    SecurityContext.set_current_user("auditor-1", RoleEnum.SENIOR_AUDITOR)

    with db_manager.session_scope() as session:
        from finauditpro.domain.entities import (
            AuditTypeEnum,
            Client,
            Engagement,
            EngagementStatusEnum,
            Firm,
        )
        from finauditpro.infrastructure.persistence.repositories import (
            ClientRepository,
            EngagementRepository,
            FirmRepository,
        )

        FirmRepository(session).add(
            Firm(id="firm-450", name="Test CA Firm", registration_number="FRN12345")
        )
        ClientRepository(session).add(
            Client(id="client-450", firm_id="firm-450", name="Test Client", pan="ABCDE1234F")
        )
        EngagementRepository(session).add(
            Engagement(
                id="eng-test-450",
                firm_id="firm-450",
                client_id="client-450",
                title="Statutory Audit FY 2025-26",
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        session.flush()

        core_repo = CoreAuditEngineRepository(session)
        misst = AuditMisstatement(
            engagement_id="eng-test-450",
            account_code="40001",
            account_name="Sales Revenue",
            schedule_iii_category="Revenue",
            amount_paise=25000000,  # ₹2,50,000
            rationale="Unearned revenue included in current year sales",
            created_by="Auditor",
        )
        core_repo.add_misstatement(misst)

    service = AuditCompletionService(db_manager)
    summary_dto = service.evaluate_sa450_misstatements("eng-test-450")

    assert summary_dto.total_identified_misstatements == 1
    assert summary_dto.total_uncorrected_misstatements == 1
    assert summary_dto.total_uncorrected_amount_paise == 25000000
    assert len(summary_dto.misstatements) == 1
    assert summary_dto.misstatements[0].title == "Sales Revenue"

