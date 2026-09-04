"""Pure domain entities for Core Audit Engine: Test Execution, Exceptions, Misstatements, and Quality Gates."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.audit_matrix_entities import AssertionEnum
from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class RiskClassificationEnum(StrEnum):
    FS_LEVEL = "Financial Statement Level Risk"
    ASSERTION_LEVEL = "Assertion Level Risk"
    SIGNIFICANT_RISK = "Significant Risk"
    FRAUD_RISK = "Fraud Risk"  # ignore
    CONTROL_RISK = "Control Risk"
    INHERENT_RISK = "Inherent Risk"
    DETECTION_RISK = "Detection Risk"
    IT_RISK = "IT-related Risk"


class ProcedureTypeClassificationEnum(StrEnum):
    INSPECTION = "Inspection"
    OBSERVATION = "Observation"
    INQUIRY = "Inquiry"
    CONFIRMATION = "Confirmation"
    RECALCULATION = "Recalculation"
    REPERFORMANCE = "Reperformance"
    ANALYTICAL_PROCEDURE = "Analytical Procedure"
    SUBSTANTIVE_TEST = "Substantive Test"
    CONTROL_TEST = "Control Test"
    WALKTHROUGH = "Walkthrough"


class AuditTestOutcomeEnum(StrEnum):
    PASS = "PASS"  # noqa: S105
    EXCEPTION = "EXCEPTION"
    FAIL = "FAIL"


class ProcedureConclusionEnum(StrEnum):
    PASS = "PASS"  # noqa: S105
    FAIL = "FAIL"
    EXCEPTION = "EXCEPTION"
    NOT_APPLICABLE = "NOT APPLICABLE"
    INCONCLUSIVE = "INCONCLUSIVE"


class ExceptionStatusEnum(StrEnum):
    OPEN = "Open"
    UNDER_INVESTIGATION = "Under Investigation"
    RESOLVED = "Resolved"
    ESCALATED_TO_MISSTATEMENT = "Escalated to Misstatement"
    DISMISSED = "Dismissed"


class MisstatementTypeEnum(StrEnum):
    FACTUAL = "Factual"
    JUDGMENTAL = "Judgmental"
    PROJECTED = "Projected"


class MisstatementStatusEnum(StrEnum):
    KNOWN = "Known"
    ESTIMATED = "Estimated"
    CORRECTED = "Corrected"
    UNCORRECTED = "Uncorrected"


class AuditSampleItemTest(DomainBaseModel):
    """Execution outcome for an individual sampled audit transaction."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    procedure_id: str = Field(...)
    sample_plan_id: str | None = Field(default=None)
    item_identifier: str = Field(..., min_length=1)
    account_code: str | None = Field(default=None)
    expected_value_paise: int = Field(default=0)
    actual_value_paise: int = Field(default=0)
    difference_paise: int = Field(default=0)
    test_result: AuditTestOutcomeEnum = Field(default=AuditTestOutcomeEnum.PASS)
    explanation: str = Field(default="")
    evidence_ref: str | None = Field(default=None)
    tested_by: str = Field(default="Auditor")
    created_at: datetime = Field(default_factory=utc_now)

    def calculate_difference(self) -> int:
        self.difference_paise = self.actual_value_paise - self.expected_value_paise
        if self.difference_paise != 0:
            self.test_result = AuditTestOutcomeEnum.EXCEPTION
        return self.difference_paise


class AuditException(DomainBaseModel):
    """First-class audit exception resulting from sample execution or substantive testing."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    procedure_id: str = Field(...)
    sample_item_id: str | None = Field(default=None)
    exception_code: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    amount_paise: int = Field(default=0, ge=0)
    root_cause: str = Field(default="")
    management_response: str = Field(default="")
    is_resolved: bool = Field(default=False)
    resolution: str = Field(default="")
    status: ExceptionStatusEnum = Field(default=ExceptionStatusEnum.OPEN)
    evidence_id: str | None = Field(default=None)
    reviewer: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AuditMisstatement(DomainBaseModel):
    """First-class financial misstatement evaluated under SA 450."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    exception_id: str | None = Field(default=None)
    procedure_id: str | None = Field(default=None)
    account_code: str = Field(...)
    account_name: str = Field(default="")
    schedule_iii_category: str = Field(default="")
    misstatement_type: MisstatementTypeEnum = Field(default=MisstatementTypeEnum.FACTUAL)
    status: MisstatementStatusEnum = Field(default=MisstatementStatusEnum.UNCORRECTED)
    amount_paise: int = Field(..., ge=0)
    is_corrected: bool = Field(default=False)
    linked_aje_id: str | None = Field(default=None)
    linked_aje_number: str | None = Field(default=None)
    rationale: str = Field(default="")
    created_by: str = Field(default="Auditor")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AssertionCoverageMatrixLine(DomainBaseModel):
    """Line in the Assertion Coverage Matrix."""

    account_or_area: str
    schedule_iii_category: str
    assertion: AssertionEnum
    linked_risk_codes: list[str] = Field(default_factory=list)
    linked_procedure_codes: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    has_conclusion: bool = False
    is_covered: bool = False
    gap_reason: str | None = None


class AssertionCoverageReport(DomainBaseModel):
    """Full engagement assertion coverage evaluation."""

    total_matrix_lines: int
    covered_lines: int
    gap_count: int
    coverage_percentage: float
    gaps: list[str]
    lines: list[AssertionCoverageMatrixLine]


class AuditCompletenessReport(DomainBaseModel):
    """Deterministic 6-factor audit completeness calculation."""

    engagement_id: str
    risk_coverage_pct: float
    procedure_execution_pct: float
    evidence_coverage_pct: float
    exception_resolution_pct: float
    misstatement_resolution_pct: float
    review_completion_pct: float
    composite_completeness_score: float
    is_ready_for_finalization: bool
    orphaned_risks: list[str] = Field(default_factory=list)
    orphaned_procedures: list[str] = Field(default_factory=list)
    procedures_missing_evidence: list[str] = Field(default_factory=list)
    procedures_missing_conclusion: list[str] = Field(default_factory=list)
    unresolved_exceptions: list[str] = Field(default_factory=list)
    unresolved_misstatements: list[str] = Field(default_factory=list)


class MisstatementAggregationSummary(DomainBaseModel):
    """SA 450 summary of misstatements compared against engagement materiality thresholds."""

    overall_materiality_paise: int
    performance_materiality_paise: int
    clearly_trivial_threshold_paise: int
    total_factual_paise: int
    total_judgmental_paise: int
    total_projected_paise: int
    total_known_misstatement_paise: int
    total_uncorrected_misstatement_paise: int
    total_corrected_misstatement_paise: int
    remaining_materiality_headroom_paise: int
    is_material_misstatement_present: bool
    requires_modified_opinion: bool
