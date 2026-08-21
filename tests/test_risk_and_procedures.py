"""Tests for Qualitative Risk Register, Assertion Sets, and Audit Procedures."""

from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditProcedure,
    AuditRisk,
    RiskSeverityEnum,
    derive_qualitative_romm,
)


def test_qualitative_romm_matrix() -> None:
    """Verify 3x3 qualitative matrix derivation for Risk of Material Misstatement."""
    assert derive_qualitative_romm(RiskSeverityEnum.HIGH, RiskSeverityEnum.MEDIUM) == RiskSeverityEnum.HIGH
    assert derive_qualitative_romm(RiskSeverityEnum.MEDIUM, RiskSeverityEnum.HIGH) == RiskSeverityEnum.HIGH
    assert derive_qualitative_romm(RiskSeverityEnum.MEDIUM, RiskSeverityEnum.LOW) == RiskSeverityEnum.MEDIUM
    assert derive_qualitative_romm(RiskSeverityEnum.LOW, RiskSeverityEnum.LOW) == RiskSeverityEnum.LOW


def test_risk_assertion_mapping() -> None:
    """Verify audit risk assertion set mapping."""
    risk = AuditRisk(
        engagement_id="eng-test-1",
        risk_code="RSK-01",
        title="Unrecorded Sales Cut-Off",
        category="Revenue Recognition",
        description="Potential understatement of year-end sales revenue.",
        assertions=[AssertionEnum.COMPLETENESS, AssertionEnum.CUT_OFF],
        inherent_risk=RiskSeverityEnum.HIGH,
        control_risk=RiskSeverityEnum.MEDIUM,
    )
    risk.calculate_romm()

    assert risk.derived_romm == RiskSeverityEnum.HIGH
    assert AssertionEnum.COMPLETENESS in risk.assertions
    assert AssertionEnum.CUT_OFF in risk.assertions


def test_procedure_risk_linking() -> None:
    """Verify audit procedure creation with linked risk IDs and target assertions."""
    proc = AuditProcedure(
        engagement_id="eng-test-1",
        procedure_code="PROC-01",
        objective="Perform year-end sales cutoff testing on invoice samples.",
        procedure_type="Substantive Test of Details",
        linked_risk_ids=["risk-101", "risk-102"],
        assertions=[AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY],
    )

    assert proc.procedure_code == "PROC-01"
    assert "risk-101" in proc.linked_risk_ids
    assert "risk-102" in proc.linked_risk_ids
    assert AssertionEnum.CUT_OFF in proc.assertions
