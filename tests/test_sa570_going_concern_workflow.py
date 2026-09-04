"""Tests for SA 570 Going Concern Evaluation, Solvency Multi-Factor Logic, and Partner Sign-Off."""

import pytest

from finauditpro.application.audit_completion_dtos import (
    CreateGoingConcernAssessmentDTO,
    GoingConcernMitigationDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_completion_service import AuditCompletionService
from finauditpro.domain.audit_completion_engine import AuditCompletionEngine
from finauditpro.domain.audit_completion_entities import (
    GoingConcernConclusionEnum,
    GoingConcernMitigation,
    SolvencyRiskLevelEnum,
)
from finauditpro.domain.exceptions import PermissionDeniedError
from finauditpro.infrastructure.first_run import initialize_database


def test_sa570_pure_engine_solvent_scenario() -> None:
    risk, is_uncertain, conclusion, rationale = (
        AuditCompletionEngine.evaluate_sa570_going_concern(
            has_operating_losses=False,
            has_negative_operating_cashflow=False,
            has_negative_net_worth=False,
            has_covenant_breaches=False,
            has_delayed_statutory_dues=False,
            has_debt_maturity_unfunded=False,
            current_ratio=1.45,
            debt_equity_ratio=0.60,
            mitigations=[],
        )
    )

    assert risk == SolvencyRiskLevelEnum.LOW
    assert not is_uncertain
    assert conclusion == GoingConcernConclusionEnum.NO_MATERIAL_UNCERTAINTY
    assert "12-month look-forward period" in rationale


def test_sa570_pure_engine_critical_distress_with_feasible_mitigation() -> None:
    mitigations = [
        GoingConcernMitigation(
            factor_title="Debt restructuring",
            management_plan="Sanction letter received from SBI for 5-year term loan restructuring",
            auditor_evaluation="Verified sanction letter and board resolution",
            is_feasible=True,
        )
    ]

    risk, is_uncertain, conclusion, rationale = (
        AuditCompletionEngine.evaluate_sa570_going_concern(
            has_operating_losses=True,
            has_negative_operating_cashflow=True,
            has_negative_net_worth=True,
            has_covenant_breaches=True,
            has_delayed_statutory_dues=False,
            has_debt_maturity_unfunded=True,
            current_ratio=0.72,
            debt_equity_ratio=3.5,
            mitigations=mitigations,
        )
    )

    assert risk == SolvencyRiskLevelEnum.CRITICAL_GOING_CONCERN_RISK
    assert is_uncertain
    assert (
        conclusion
        == GoingConcernConclusionEnum.MATERIAL_UNCERTAINTY_ADEQUATELY_DISCLOSED
    )
    assert "Material Uncertainty paragraph" in rationale


def test_sa570_service_rbac_partner_signoff(tmp_path: any) -> None:
    db_path = tmp_path / "test_sa570.db"
    db_manager = initialize_database(db_path)

    service = AuditCompletionService(db_manager)

    # 1. Senior Auditor cannot do partner sign-off
    SecurityContext.set_current_user("auditor-1", RoleEnum.SENIOR_AUDITOR)
    dto_unauth = CreateGoingConcernAssessmentDTO(
        current_ratio=1.5,
        debt_equity_ratio=0.5,
        partner_signoff=True,
    )
    with pytest.raises(PermissionDeniedError):
        service.create_or_update_going_concern_assessment("eng-test-570", dto_unauth)

    # 2. Partner CAN do partner sign-off
    SecurityContext.set_current_user("partner-1", RoleEnum.PARTNER)
    dto_auth = CreateGoingConcernAssessmentDTO(
        current_ratio=1.5,
        debt_equity_ratio=0.5,
        partner_signoff=True,
        reviewer="Partner Jane Doe",
    )
    res = service.create_or_update_going_concern_assessment("eng-test-570", dto_auth)
    assert res.partner_signoff
    assert res.reviewer == "Partner Jane Doe"
    assert res.audit_conclusion == GoingConcernConclusionEnum.NO_MATERIAL_UNCERTAINTY.value
