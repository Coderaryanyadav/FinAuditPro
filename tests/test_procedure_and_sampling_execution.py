"""Tests for Audit Procedure Engine, MUS Sampling Execution, and Conclusion Consistency Guardrails."""

import pytest

from finauditpro.application.audit_matrix_dtos import CreateProcedureDTO
from finauditpro.application.core_audit_dtos import (
    EvaluateProcedureConclusionDTO,
    ExecuteSampleItemTestDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.audit_execution_entities import (
    AuditTestOutcomeEnum,
    ProcedureConclusionEnum,
)
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
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
from finauditpro.domain.exceptions import ValidationError
from finauditpro.domain.sampling_engine import AuditSamplingEngine
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
    db_path = tmp_path / "test_proc_engine.db"
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


def test_procedure_sampling_and_test_line_execution(db_manager, seed_engagement):
    """Verify procedure sampling execution, difference paise calculations, and item logging."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_engagement.id,
            procedure_code="PRC-EXP-001",
            objective="Vouching of Repair & Maintenance expenses against invoices",
            assertions=[AssertionEnum.OCCURRENCE, AssertionEnum.ACCURACY],
            procedure_type="Substantive Test",
        )
    )

    # 1. Execute MUS Sampling on Population
    pop_records = [
        {"voucher_no": "VR-101", "amount_paise": 5000000},  # ₹50,000
        {"voucher_no": "VR-102", "amount_paise": 150000000},  # ₹15,00,000 (High-value)
        {"voucher_no": "VR-103", "amount_paise": 2000000},  # ₹20,000
        {"voucher_no": "VR-104", "amount_paise": 80000000},  # ₹8,00,000
    ]
    sampling_res = AuditSamplingEngine.calculate_mus_sample(
        population_records=pop_records,
        tolerable_misstatement_paise=50000000,  # ₹5,00,000
        confidence_level_pct=95.0,
    )
    assert sampling_res.sample_size >= 1
    assert len(sampling_res.high_value_items) >= 1  # VR-102 is stratified as high-value

    # 2. Execute Sample Item Tests
    item_pass = core_svc.execute_sample_item_test(
        ExecuteSampleItemTestDTO(
            procedure_id=proc.id,
            item_identifier="VR-101",
            expected_value_paise=5000000,
            actual_value_paise=5000000,
            explanation="Invoice verified and agrees with general ledger entry",
            evidence_ref="INV-101.pdf",
        )
    )
    assert item_pass.difference_paise == 0
    assert item_pass.test_result == AuditTestOutcomeEnum.PASS

    item_fail = core_svc.execute_sample_item_test(
        ExecuteSampleItemTestDTO(
            procedure_id=proc.id,
            item_identifier="VR-102",
            expected_value_paise=150000000,
            actual_value_paise=145000000,
            explanation="GST input credit ₹50,000 uncredited and wrongly capitalized as expense",
            evidence_ref="INV-102.pdf",
        )
    )
    assert item_fail.difference_paise == -5000000
    assert item_fail.test_result == AuditTestOutcomeEnum.EXCEPTION


def test_conclusion_consistency_guardrail(db_manager, seed_engagement):
    """Verify that Test = EXCEPTION/FAIL cannot have Conclusion = PASS without an explicit documented override."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_engagement.id,
            procedure_code="PRC-SALES-001",
            objective="Testing sales cutoff around balance sheet date",
            assertions=[AssertionEnum.CUT_OFF],
            procedure_type="Substantive Test",
        )
    )

    # Record a failed test item
    core_svc.execute_sample_item_test(
        ExecuteSampleItemTestDTO(
            procedure_id=proc.id,
            item_identifier="INV-9999",
            expected_value_paise=25000000,
            actual_value_paise=20000000,
            explanation="Goods dispatched on April 2 wrongly booked in March",
        )
    )

    # 1. Attempt to set Conclusion to PASS without override -> MUST BE REJECTED
    with pytest.raises(ValidationError, match="Inconsistent Conclusion"):
        core_svc.evaluate_procedure_conclusion(
            EvaluateProcedureConclusionDTO(
                engagement_id=seed_engagement.id,
                procedure_id=proc.id,
                conclusion=ProcedureConclusionEnum.PASS,
                result_summary="All tests completed successfully without exceptions",
                override_reason=None,
            )
        )

    # 2. Set Conclusion to PASS WITH documented override rationale -> MUST SUCCEED
    updated = core_svc.evaluate_procedure_conclusion(
        EvaluateProcedureConclusionDTO(
            engagement_id=seed_engagement.id,
            procedure_id=proc.id,
            conclusion=ProcedureConclusionEnum.PASS,
            result_summary="Exception quantified and isolated; management agreed to AJE",
            override_reason="Isolated cutoff timing variance below performance materiality, adjusted via AJE-001",
        )
    )
    assert updated.status == ProcedureStatusEnum.COMPLETED
    assert updated.conclusion == "PASS"
