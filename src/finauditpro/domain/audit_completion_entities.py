"""Pure domain entities and enumerations for Phase D: Audit Completion & Misstatement Evaluation.

Covers ICAI Standards on Auditing:
- SA 450: Evaluation of Misstatements Identified during the Audit
- SA 570 (Revised): Going Concern
- SA 580: Written Representations (Management Representation Letter)
- SA 560: Subsequent Events
- SA 520: Analytical Procedures (Final Review at Completion)
"""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


# ==========================================
# SA 450: Evaluation of Misstatements
# ==========================================


class MisstatementTypeEnum(StrEnum):
    FACTUAL = "Factual Misstatement"
    JUDGMENTAL = "Judgmental Misstatement"
    PROJECTED = "Projected Misstatement"


class MisstatementStatusEnum(StrEnum):
    IDENTIFIED = "Identified"
    CORRECTED = "Corrected by Management"
    UNCORRECTED = "Uncorrected / Passed"


class SA450AuditConclusionEnum(StrEnum):
    UNQUALIFIED_ACCEPTABLE = "Unqualified: Uncorrected misstatements are immaterial individually and in aggregate"
    MANAGEMENT_CORRECTION_REQUIRED = (
        "Correction Required: Uncorrected misstatements exceed Materiality"
    )
    MODIFIED_OPINION_REQUIRED = (
        "Modified Opinion Required: Management refused to correct material misstatements"
    )


class FinancialMisstatement(DomainBaseModel):
    """First-class financial misstatement evaluated under SA 450."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    misstatement_number: str = Field(...)
    misstatement_type: MisstatementTypeEnum = Field(default=MisstatementTypeEnum.FACTUAL)
    status: MisstatementStatusEnum = Field(default=MisstatementStatusEnum.IDENTIFIED)
    title: str = Field(...)
    description: str = Field(...)
    affected_fs_area: str = Field(...)
    amount_paise: int = Field(..., ge=0)
    is_pnl_impact: bool = Field(default=True)
    pnl_overstatement_paise: int = Field(default=0)
    is_balance_sheet_impact: bool = Field(default=True)
    balance_sheet_overstatement_paise: int = Field(default=0)
    is_clearly_trivial: bool = Field(default=False)
    working_paper_ref: str | None = Field(default=None)
    linked_aje_id: str | None = Field(default=None)
    management_response: str | None = Field(default=None)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class SA450EvaluationSummary(DomainBaseModel):
    """Summary of uncorrected misstatements evaluated against engagement materiality."""

    engagement_id: str
    overall_materiality_paise: int
    performance_materiality_paise: int
    clearly_trivial_threshold_paise: int
    total_identified_misstatements: int
    total_corrected_misstatements: int
    total_uncorrected_misstatements: int
    total_uncorrected_amount_paise: int
    total_uncorrected_pnl_impact_paise: int
    total_uncorrected_bs_impact_paise: int
    is_material_individually: bool
    is_material_in_aggregate: bool
    requires_opinion_modification: bool
    audit_conclusion: SA450AuditConclusionEnum
    evaluated_misstatements: list[FinancialMisstatement] = Field(default_factory=list)


# ==========================================
# SA 570: Going Concern
# ==========================================


class SolvencyRiskLevelEnum(StrEnum):
    LOW = "Low / Normal Operating Cycle"
    ELEVATED = "Elevated Material Uncertainty"
    CRITICAL_GOING_CONCERN_RISK = "Critical Going Concern Risk"


class GoingConcernConclusionEnum(StrEnum):
    NO_MATERIAL_UNCERTAINTY = (
        "Going concern basis appropriate; no material uncertainty identified"
    )
    MATERIAL_UNCERTAINTY_ADEQUATELY_DISCLOSED = (
        "Material uncertainty exists; adequately disclosed in Notes to Accounts (SA 570 §22)"
    )
    MATERIAL_UNCERTAINTY_NOT_ADEQUATELY_DISCLOSED = (
        "Material uncertainty exists; NOT adequately disclosed (Qualified/Adverse Opinion SA 705)"
    )
    GOING_CONCERN_INAPPROPRIATE = (
        "Use of going concern basis is inappropriate (Adverse Opinion SA 705)"
    )


class GoingConcernMitigation(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    factor_title: str = Field(...)
    management_plan: str = Field(...)
    auditor_evaluation: str = Field(...)
    is_feasible: bool = Field(default=True)


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
    current_ratio: float = Field(default=1.0)
    debt_equity_ratio: float = Field(default=0.0)
    solvency_risk_level: SolvencyRiskLevelEnum = Field(default=SolvencyRiskLevelEnum.LOW)
    material_uncertainty_identified: bool = Field(default=False)
    mitigations: list[GoingConcernMitigation] = Field(default_factory=list)
    audit_conclusion: GoingConcernConclusionEnum = Field(
        default=GoingConcernConclusionEnum.NO_MATERIAL_UNCERTAINTY
    )
    conclusion_rationale: str = Field(default="")
    preparer: str = Field(default="Senior Auditor")
    reviewer: str | None = Field(default=None)
    partner_signoff: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


# ==========================================
# SA 580: Written Representations (MRL)
# ==========================================


class MRLStatusEnum(StrEnum):
    DRAFT = "Draft Representation Letter"
    DISPATCHED = "Dispatched to Management"
    SIGNED_AND_OBTAINED = "Signed Representation Letter Obtained"
    SIGNED_BY_MANAGEMENT = "Signed by Management"
    REFUSED_BY_MANAGEMENT = "Refused by Management (Scope Limitation)"


class MRLClauseCategoryEnum(StrEnum):
    GENERAL_RESPONSIBILITY = "Management Responsibility for Financial Statements"
    INTERNAL_CONTROL_AND_IRREGULARITIES = "Internal Controls & Non-Compliance Reporting"
    GOING_CONCERN = "Going Concern & 12-Month Solvency"
    SUBSEQUENT_EVENTS = "Subsequent Events Disclosure (SA 560)"
    RELATED_PARTIES = "Related Party Disclosures & Transactions"
    LITIGATION_AND_CLAIMS = "Litigations, Claims & Contingent Liabilities"
    STATUTORY_COMPLIANCE = "CARO 2020 & Form 3CD Tax Declarations"


class MRLClause(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    clause_number: str = Field(...)
    category: MRLClauseCategoryEnum = Field(...)
    title: str = Field(...)
    text_content: str = Field(...)
    is_mandatory: bool = Field(default=True)
    is_accepted_by_management: bool = Field(default=True)
    is_modified: bool = Field(default=False)
    specific_facts: str | None = Field(default=None)


class ManagementRepresentationLetter(DomainBaseModel):
    """SA 580 Management Representation Letter record."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    mrl_number: str = Field(...)
    financial_year: str = Field(...)
    status: MRLStatusEnum = Field(default=MRLStatusEnum.DRAFT)
    requested_date: str = Field(...)
    signed_date: str | None = Field(default=None)
    signatory_name: str | None = Field(default=None)
    signatory_designation: str | None = Field(default=None)
    audit_report_date: str | None = Field(default=None)
    clauses: list[MRLClause] = Field(default_factory=list)
    is_chronologically_valid: bool = Field(default=True)
    chronology_validation_msg: str | None = Field(default=None)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


# ==========================================
# SA 560: Subsequent Events
# ==========================================


class SubsequentEventTypeEnum(StrEnum):
    TYPE_I_ADJUSTING = "Type I: Adjusting Event (Conditions existing at Balance Sheet date)"
    TYPE_II_NON_ADJUSTING = (
        "Type II: Non-Adjusting Event (Conditions arising after Balance Sheet date)"
    )
    ADJUSTING = "Type I: Adjusting Event (Conditions existing at Balance Sheet date)"
    NON_ADJUSTING = "Type II: Non-Adjusting Event (Conditions arising after Balance Sheet date)"


class SubsequentEventProcedureEnum(StrEnum):
    INTERIM_FS_REVIEW = "Review of latest available interim financial statements"
    BOARD_MINUTES_REVIEW = "Review of Board of Directors & Audit Committee minutes"
    MANAGEMENT_INQUIRY = "Inquiries of Management regarding unrecorded commitments"
    LEGAL_INQUIRY = "Inquiries of entity legal counsel on post-year-end claims"
    BANK_STATEMENTS_REVIEW = "Examination of subsequent bank statements and cash receipts"


class SubsequentEvent(DomainBaseModel):
    """Subsequent event evaluated between Balance Sheet date and Audit Report date under SA 560."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    event_date: str = Field(...)
    event_type: SubsequentEventTypeEnum = Field(...)
    description: str = Field(...)
    estimated_amount_paise: int = Field(default=0)
    accounting_treatment: str = Field(...)
    is_adjusted_in_fs: bool = Field(default=False)
    is_disclosed_in_notes: bool = Field(default=False)
    working_paper_ref: str | None = Field(default=None)
    procedure_applied: str | SubsequentEventProcedureEnum = Field(
        default=SubsequentEventProcedureEnum.MANAGEMENT_INQUIRY
    )
    auditor_conclusion: str = Field(default="")
    identified_by: str = Field(default="Auditor")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


# ==========================================
# SA 520: Final Analytical Review
# ==========================================


class RatioCategoryEnum(StrEnum):
    LIQUIDITY = "Liquidity Ratios"
    PROFITABILITY = "Profitability Ratios"
    SOLVENCY = "Solvency & Leverage Ratios"
    TURNOVER = "Turnover & Operating Cycle Ratios"


class RatioComparisonLine(DomainBaseModel):
    ratio_name: str
    category: RatioCategoryEnum
    current_year_value: float
    previous_year_value: float
    variance_percentage: float
    is_significant_variance: bool
    auditor_explanation: str = ""


class FinalAnalyticalReview(DomainBaseModel):
    """SA 520 overall analytical review performed at audit completion."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    ratio_lines: list[RatioComparisonLine] = Field(default_factory=list)
    has_unexplained_significant_variances: bool = Field(default=False)
    overall_consistency_conclusion: str = Field(...)
    completed_by: str = Field(default="Senior Auditor")
    reviewed_by: str | None = Field(default=None)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
