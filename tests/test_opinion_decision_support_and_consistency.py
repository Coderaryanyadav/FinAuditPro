"""Unit tests for Phase E: Opinion Decision Support, Consistency Engine, and Candidate KAM Detection."""


from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    CandidateKAMSourceEnum,
    OpinionFactorEnum,
)
from finauditpro.domain.opinion_consistency_engine import OpinionConsistencyEngine


def test_opinion_decision_support_unmodified_clean() -> None:
    res = OpinionConsistencyEngine.evaluate_opinion_consistency(
        proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        materiality_paise=10000000,  # 1 Lakh
        uncorrected_misstatements_paise=1000000,  # 10k (trivial, well below materiality)
        has_scope_limitation=False,
        is_scope_limitation_pervasive=False,
        has_going_concern_uncertainty=False,
        is_going_concern_disclosed=True,
    )
    assert res.is_consistent is True
    assert res.review_required is False
    assert len(res.identified_factors) == 0
    assert "consistent" in res.suggested_assessment.lower()


def test_opinion_decision_support_flags_material_misstatement() -> None:
    # Uncorrected misstatement exceeds materiality (1.5 Lakhs vs 1 Lakh materiality)
    res = OpinionConsistencyEngine.evaluate_opinion_consistency(
        proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        materiality_paise=10000000,
        uncorrected_misstatements_paise=15000000,
        has_scope_limitation=False,
        is_scope_limitation_pervasive=False,
        has_going_concern_uncertainty=False,
        is_going_concern_disclosed=True,
    )
    assert res.is_consistent is False
    assert res.review_required is True
    assert OpinionFactorEnum.MATERIAL_MISSTATEMENT in res.identified_factors
    assert OpinionFactorEnum.MATERIAL_NOT_PERVASIVE in res.identified_factors
    assert "Qualified Opinion" in res.suggested_assessment


def test_opinion_decision_support_flags_pervasive_misstatement() -> None:
    # Misstatement is 4x materiality -> Material and Pervasive
    res = OpinionConsistencyEngine.evaluate_opinion_consistency(
        proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        materiality_paise=10000000,
        uncorrected_misstatements_paise=40000000,
        has_scope_limitation=False,
        is_scope_limitation_pervasive=False,
        has_going_concern_uncertainty=False,
        is_going_concern_disclosed=True,
    )
    assert res.is_consistent is False
    assert res.review_required is True
    assert OpinionFactorEnum.MATERIAL_AND_PERVASIVE in res.identified_factors
    assert "Adverse Opinion" in res.suggested_assessment


def test_opinion_decision_support_scope_limitation() -> None:
    res = OpinionConsistencyEngine.evaluate_opinion_consistency(
        proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        materiality_paise=10000000,
        uncorrected_misstatements_paise=0,
        has_scope_limitation=True,
        is_scope_limitation_pervasive=True,
        has_going_concern_uncertainty=False,
        is_going_concern_disclosed=True,
    )
    assert res.is_consistent is False
    assert res.review_required is True
    assert "Disclaimer of Opinion" in res.suggested_assessment


def test_candidate_kam_detection() -> None:
    risks = [
        {"id": "R1", "title": "Revenue Cut-off Risk", "risk_level": "High", "assertion": "Cut-off"},
        {"id": "R2", "title": "Routine Bank Reconciliations", "risk_level": "Low", "assertion": "Existence"},
    ]
    ajes = [
        {"id": "AJE-1", "amount_paise": 60000000, "description": "Inventory NRV write-down"},
        {"id": "AJE-2", "amount_paise": 50000, "description": "Minor prepaid expense"},
    ]
    candidates = OpinionConsistencyEngine.detect_candidate_kams(
        significant_risks=risks,
        major_audit_adjustments=ajes,
        materiality_paise=100000000,  # 10 Lakhs
    )
    assert len(candidates) == 2
    assert all(c.is_candidate for c in candidates)
    assert candidates[0].candidate_source == CandidateKAMSourceEnum.SIGNIFICANT_RISK
    assert candidates[1].candidate_source == CandidateKAMSourceEnum.MAJOR_ADJUSTMENT


def test_cross_document_consistency_checks() -> None:
    issues = OpinionConsistencyEngine.check_cross_document_consistency(
        fs_revenue_paise=1000000000,
        tb_revenue_paise=950000000,  # mismatch!
        fs_profit_paise=150000000,
        pnl_profit_paise=150000000,
        fs_net_worth_paise=500000000,
        bs_net_worth_paise=500000000,
        caro_report_answers={"3(i)": "Unqualified", "3(ii)": "Qualified"},
        caro_workpaper_answers={"3(i)": "Unqualified", "3(ii)": "Unqualified"},  # mismatch on 3(ii)!
        going_concern_memo_uncertainty=True,
        fs_has_going_concern_note=False,  # missing note!
        mrl_signed=False,  # unsigned MRL!
    )
    assert len(issues) == 4
    categories = [i.category for i in issues]
    assert "Financial Statements vs Adjusted TB" in categories
    assert "CARO 2020 Reporting" in categories
    assert "Going Concern (SA 570)" in categories
    assert "Written Representations (SA 580)" in categories
