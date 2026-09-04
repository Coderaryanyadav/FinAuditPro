"""Data Transfer Objects (DTOs) for Phase D Audit Completion modules."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FinancialMisstatementDTO:
    id: str
    engagement_id: str
    misstatement_number: str
    misstatement_type: str
    status: str
    title: str
    description: str
    affected_fs_area: str
    amount_paise: int
    is_pnl_impact: bool
    pnl_overstatement_paise: int
    is_balance_sheet_impact: bool
    balance_sheet_overstatement_paise: int
    is_clearly_trivial: bool
    working_paper_ref: str | None
    linked_aje_id: str | None
    management_response: str | None
    created_at: str


@dataclass(frozen=True)
class CreateMisstatementDTO:
    misstatement_number: str
    misstatement_type: str
    title: str
    description: str
    affected_fs_area: str
    amount_paise: int
    is_pnl_impact: bool = True
    pnl_overstatement_paise: int = 0
    is_balance_sheet_impact: bool = True
    balance_sheet_overstatement_paise: int = 0
    working_paper_ref: str | None = None
    linked_aje_id: str | None = None


@dataclass(frozen=True)
class SA450EvaluationSummaryDTO:
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
    audit_conclusion: str
    misstatements: list[FinancialMisstatementDTO] = field(default_factory=list)


@dataclass(frozen=True)
class GoingConcernMitigationDTO:
    id: str
    factor_title: str
    management_plan: str
    auditor_evaluation: str
    is_feasible: bool = True


@dataclass(frozen=True)
class GoingConcernAssessmentDTO:
    id: str
    engagement_id: str
    assessment_period_months: int
    has_operating_losses: bool
    has_negative_operating_cashflow: bool
    has_negative_net_worth: bool
    has_covenant_breaches: bool
    has_delayed_statutory_dues: bool
    has_debt_maturity_unfunded: bool
    current_ratio: float
    debt_equity_ratio: float
    solvency_risk_level: str
    material_uncertainty_identified: bool
    mitigations: list[GoingConcernMitigationDTO]
    audit_conclusion: str
    conclusion_rationale: str
    preparer: str
    reviewer: str | None
    partner_signoff: bool
    created_at: str


@dataclass(frozen=True)
class CreateGoingConcernAssessmentDTO:
    has_operating_losses: bool = False
    has_negative_operating_cashflow: bool = False
    has_negative_net_worth: bool = False
    has_covenant_breaches: bool = False
    has_delayed_statutory_dues: bool = False
    has_debt_maturity_unfunded: bool = False
    current_ratio: float = 1.0
    debt_equity_ratio: float = 0.0
    mitigations: list[GoingConcernMitigationDTO] = field(default_factory=list)
    preparer: str = "Senior Auditor"
    reviewer: str | None = None
    partner_signoff: bool = False


@dataclass(frozen=True)
class MRLClauseDTO:
    id: str
    clause_number: str
    category: str
    title: str
    text_content: str
    is_mandatory: bool = True
    is_accepted_by_management: bool = True
    is_modified: bool = False
    specific_facts: str | None = None


@dataclass(frozen=True)
class ManagementRepresentationLetterDTO:
    id: str
    engagement_id: str
    mrl_number: str
    financial_year: str
    status: str
    requested_date: str
    signed_date: str | None
    signatory_name: str | None
    signatory_designation: str | None
    clauses: list[MRLClauseDTO]
    is_chronologically_valid: bool
    created_at: str
    audit_report_date: str | None = None
    chronology_validation_msg: str | None = None


@dataclass(frozen=True)
class SubsequentEventDTO:
    id: str
    engagement_id: str
    event_date: str
    event_type: str
    description: str
    estimated_amount_paise: int
    accounting_treatment: str
    is_adjusted_in_fs: bool
    is_disclosed_in_notes: bool
    working_paper_ref: str | None
    procedure_applied: str
    auditor_conclusion: str
    created_at: str
    identified_by: str | None = None


@dataclass(frozen=True)
class CreateSubsequentEventDTO:
    event_date: str
    event_type: str
    description: str
    estimated_amount_paise: int
    accounting_treatment: str
    is_adjusted_in_fs: bool = False
    is_disclosed_in_notes: bool = False
    working_paper_ref: str | None = None
    procedure_applied: str = "Review of latest available interim financial statements"
    auditor_conclusion: str = ""


@dataclass(frozen=True)
class RatioComparisonLineDTO:
    ratio_name: str
    category: str
    current_year_value: float
    previous_year_value: float
    variance_percentage: float
    is_significant_variance: bool
    auditor_explanation: str


@dataclass(frozen=True)
class FinalAnalyticalReviewDTO:
    id: str
    engagement_id: str
    ratio_lines: list[RatioComparisonLineDTO]
    has_unexplained_significant_variances: bool
    overall_consistency_conclusion: str
    completed_by: str
    reviewed_by: str | None
    created_at: str
