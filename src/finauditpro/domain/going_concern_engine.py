"""Pure domain entities and evaluation algorithms for SA 570 (Revised) Going Concern assessments."""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class SolvencyRiskLevelEnum(StrEnum):
    LOW = "Low / Normal Operating Cycle"
    ELEVATED = "Elevated Material Uncertainty"
    CRITICAL_GOING_CONCERN_RISK = "Critical Going Concern Risk"


class GoingConcernMitigation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    factor_title: str = Field(...)
    management_plan: str = Field(...)
    auditor_evaluation: str = Field(...)
    is_feasible: bool = Field(default=True)


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class GoingConcernAssessment(DomainBaseModel):
    """SA 570 structured 12-month solvency and going concern assessment memo."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    assessment_period_months: int = Field(default=12, ge=12)
    has_operating_losses: bool = Field(default=False)
    has_negative_operating_cashflow: bool = Field(default=False)
    has_negative_net_worth: bool = Field(default=False)
    has_covenant_breaches: bool = Field(default=False)
    has_delayed_statutory_dues: bool = Field(default=False)
    has_debt_maturity_unfunded: bool = Field(default=False)
    solvency_risk_level: SolvencyRiskLevelEnum = Field(default=SolvencyRiskLevelEnum.LOW)
    conclusion_rationale: str = Field(default="")
    material_uncertainty_identified: bool = Field(default=False)
    report_disclosure_required: bool = Field(default=False)
    mitigations: list[GoingConcernMitigation] = Field(default_factory=list)
    preparer: str = Field(default="Senior Auditor")
    reviewer: str | None = Field(default=None)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class GoingConcernEngine:
    """Deterministic evaluation engine for SA 570 Going Concern indicators."""

    @classmethod
    def evaluate_indicators(
        cls,
        has_operating_losses: bool,
        has_negative_operating_cashflow: bool,
        has_negative_net_worth: bool,
        has_covenant_breaches: bool,
        has_debt_maturity_unfunded: bool,
    ) -> tuple[SolvencyRiskLevelEnum, bool, str]:
        """Evaluate key financial indicators and determine SA 570 reporting requirements."""
        indicators_count = sum(
            [
                has_operating_losses,
                has_negative_operating_cashflow,
                has_negative_net_worth,
                has_covenant_breaches,
                has_debt_maturity_unfunded,
            ]
        )

        if has_negative_net_worth or (has_operating_losses and has_negative_operating_cashflow and has_debt_maturity_unfunded):
            return (
                SolvencyRiskLevelEnum.CRITICAL_GOING_CONCERN_RISK,
                True,
                "Material Uncertainty Related to Going Concern exists (Negative Net Worth / Unfunded Debt). Requires SA 570 / SA 705 report disclosure.",
            )
        elif indicators_count >= 2:
            return (
                SolvencyRiskLevelEnum.ELEVATED,
                True,
                "Elevated solvency indicators identified requiring auditor challenge of management mitigating cash-flow forecasts.",
            )
        else:
            return (
                SolvencyRiskLevelEnum.LOW,
                False,
                "Financial indicators support assumption of going concern over 12-month look-forward period.",
            )
