"""Domain entities for Risk, SA 320 Materiality, Audit Procedures, Findings & Evidence Matrix."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now
from finauditpro.domain.value_objects import Money


class AssertionEnum(StrEnum):
    COMPLETENESS = "Completeness"
    ACCURACY = "Accuracy"
    CUT_OFF = "Cut-Off"
    EXISTENCE = "Existence"
    VALUATION = "Valuation & Allocation"
    RIGHTS_AND_OBLIGATIONS = "Rights & Obligations"
    PRESENTATION = "Presentation & Disclosure"
    CLASSIFICATION = "Classification"
    OCCURRENCE = "Occurrence"


class RiskSeverityEnum(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ProcedureStatusEnum(StrEnum):
    NOT_STARTED = "Not Started"
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    SUBMITTED_FOR_REVIEW = "Submitted for Review"
    REVIEWED = "Reviewed"
    CLEARED = "Cleared"
    NOT_APPLICABLE = "Not Applicable"


class FindingStatusEnum(StrEnum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    RESOLVED = "Resolved"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    CARRIED_FORWARD = "Carried Forward"


class FindingSourceEnum(StrEnum):
    MANUAL = "manual"
    DETERMINISTIC_ANALYTIC = "deterministic_analytic"
    AI = "ai"


class BenchmarkTypeEnum(StrEnum):
    REVENUE = "Total Revenue"
    PROFIT_BEFORE_TAX = "Profit Before Tax (PBT)"
    TOTAL_ASSETS = "Total Assets"
    EQUITY = "Total Equity / Net Worth"


class EvidenceStatusEnum(StrEnum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    LINKED = "LINKED"
    REVIEWED = "REVIEWED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


def derive_qualitative_romm(
    inherent: RiskSeverityEnum, control: RiskSeverityEnum
) -> RiskSeverityEnum:
    """Qualitative 3x3 matrix mapping (Inherent Risk x Control Risk) -> Derived RoMM."""
    if inherent == RiskSeverityEnum.HIGH or control == RiskSeverityEnum.HIGH:
        return RiskSeverityEnum.HIGH
    if inherent == RiskSeverityEnum.MEDIUM or control == RiskSeverityEnum.MEDIUM:
        return RiskSeverityEnum.MEDIUM
    return RiskSeverityEnum.LOW


class AuditRisk(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    risk_code: str = Field(..., min_length=1)
    title: str = Field(default="Audit Risk")
    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    financial_statement_area: str = Field(default="")
    account_code: str | None = Field(default=None)
    assertions: list[AssertionEnum] = Field(default_factory=lambda: [AssertionEnum.COMPLETENESS])
    inherent_risk: RiskSeverityEnum = Field(default=RiskSeverityEnum.MEDIUM)
    control_risk: RiskSeverityEnum = Field(default=RiskSeverityEnum.MEDIUM)
    derived_romm: RiskSeverityEnum = Field(default=RiskSeverityEnum.MEDIUM)
    severity: RiskSeverityEnum = Field(default=RiskSeverityEnum.HIGH)
    magnitude: RiskSeverityEnum = Field(default=RiskSeverityEnum.HIGH)
    likelihood: RiskSeverityEnum = Field(default=RiskSeverityEnum.MEDIUM)
    risk_type: str = Field(default="Inherent Risk")
    is_significant_risk: bool = Field(default=False)
    fraud_indicator: bool = Field(default=False)  # ignore
    control_reliance: str = Field(default="No Reliance")
    planned_response: str = Field(default="")
    owner: str = Field(default="Auditor")
    status: str = Field(default="Identified")
    evidence_ids: list[str] = Field(default_factory=list)
    linked_procedure_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def calculate_romm(self) -> RiskSeverityEnum:
        self.derived_romm = derive_qualitative_romm(self.inherent_risk, self.control_risk)
        return self.derived_romm

    @property
    def area(self) -> str:
        return self.financial_statement_area

    @area.setter
    def area(self, value: str) -> None:
        self.financial_statement_area = value

    @property
    def overall_risk(self) -> RiskSeverityEnum:
        return self.derived_romm

    @overall_risk.setter
    def overall_risk(self, value: RiskSeverityEnum) -> None:
        self.derived_romm = value

    @property
    def rationale(self) -> str:
        return self.planned_response

    @rationale.setter
    def rationale(self, value: str) -> None:
        self.planned_response = value

    @property
    def evidence(self) -> list[str]:
        return self.evidence_ids

    @property
    def related_procedures(self) -> list[str]:
        return self.linked_procedure_ids

    @property
    def assertion(self) -> AssertionEnum:
        return self.assertions[0] if self.assertions else AssertionEnum.COMPLETENESS

    @property
    def risk_response(self) -> str:
        return self.planned_response

    @risk_response.setter
    def risk_response(self, value: str) -> None:
        self.planned_response = value


class MaterialityAssessment(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    benchmark_type: BenchmarkTypeEnum = Field(default=BenchmarkTypeEnum.REVENUE)
    benchmark_amount_paise: int = Field(default=0, ge=0)
    benchmark_source: str = Field(default="SA 320 Guidance (Editable Suggestion)")
    is_verified_statutory: bool = Field(default=False)
    overall_percentage: float = Field(default=1.0, ge=0.01, le=100.0)
    overall_materiality_paise: int = Field(default=0, ge=0)
    performance_percentage: float = Field(default=75.0, ge=0.01, le=100.0)
    performance_materiality_paise: int = Field(default=0, ge=0)
    trivial_percentage: float = Field(default=5.0, ge=0.01, le=100.0)
    clearly_trivial_threshold_paise: int = Field(default=0, ge=0)
    version: int = Field(default=1, ge=1)
    methodology_notes: str = Field(default="")
    rationale: str | None = Field(default=None)
    created_by: str = Field(default="Lead Auditor")
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def benchmark_amount(self) -> Money:
        return Money(paise=self.benchmark_amount_paise)

    @property
    def overall_materiality(self) -> Money:
        return Money(paise=self.overall_materiality_paise)

    @property
    def performance_materiality(self) -> Money:
        return Money(paise=self.performance_materiality_paise)

    @property
    def clearly_trivial_threshold(self) -> Money:
        return Money(paise=self.clearly_trivial_threshold_paise)


class AuditProcedure(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    procedure_code: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    procedure_type: str = Field(default="Substantive Procedure")
    account_area: str = Field(default="")
    instructions: str = Field(default="")
    evidence_requirement: str = Field(default="")
    requires_evidence: bool = Field(default=True)
    population_definition: str = Field(default="")
    linked_risk_ids: list[str] = Field(default_factory=list)
    assertions: list[AssertionEnum] = Field(default_factory=lambda: [AssertionEnum.COMPLETENESS])
    status: ProcedureStatusEnum = Field(default=ProcedureStatusEnum.NOT_STARTED)
    methodology: str = Field(default="")
    expected_result: str = Field(default="")
    actual_result: str = Field(default="")
    result_summary: str | None = Field(default=None)
    conclusion: str | None = Field(default=None)
    conclusion_override_reason: str | None = Field(default=None)
    preparer: str | None = Field(default=None)
    prepared_date: datetime | None = Field(default=None)
    reviewer: str | None = Field(default=None)
    reviewed_date: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def audit_area(self) -> str:
        return self.account_area

    @audit_area.setter
    def audit_area(self, value: str) -> None:
        self.account_area = value

    @property
    def population(self) -> str:
        return self.population_definition

    @population.setter
    def population(self, value: str) -> None:
        self.population_definition = value

    @property
    def expected_evidence(self) -> str:
        return self.evidence_requirement

    @expected_evidence.setter
    def expected_evidence(self, value: str) -> None:
        self.evidence_requirement = value

    @property
    def risk_id(self) -> str | None:
        return self.linked_risk_ids[0] if self.linked_risk_ids else None

    @risk_id.setter
    def risk_id(self, value: str | None) -> None:
        if value:
            self.linked_risk_ids = [value]


    @property
    def assertion(self) -> AssertionEnum:
        return self.assertions[0] if self.assertions else AssertionEnum.COMPLETENESS


class AuditFinding(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    procedure_id: str | None = Field(default=None)
    risk_id: str | None = Field(default=None)
    working_paper_id: str | None = Field(default=None)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    category: str = Field(default="Substantive Audit Exception")
    severity: RiskSeverityEnum = Field(default=RiskSeverityEnum.HIGH)
    amount_paise: int | None = Field(default=None, ge=0)
    affected_account: str | None = Field(default=None)
    assertion: AssertionEnum = Field(default=AssertionEnum.ACCURACY)
    recommendation: str | None = Field(default=None)
    status: FindingStatusEnum = Field(default=FindingStatusEnum.OPEN)
    resolution: str | None = Field(default=None)
    linked_exception_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    preparer: str = Field(default="Auditor")
    reviewer: str | None = Field(default=None)
    source: FindingSourceEnum = Field(default=FindingSourceEnum.MANUAL)
    is_ai_generated: bool = Field(default=False)
    prior_engagement_finding_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def monetary_amount(self) -> Money | None:
        return Money(paise=self.amount_paise) if self.amount_paise is not None else None


class AuditEvidence(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    evidence_code: str = Field(default="")
    finding_id: str | None = Field(default=None)
    procedure_id: str | None = Field(default=None)
    working_paper_id: str | None = Field(default=None)
    document_id: str | None = Field(default=None)
    dataset_id: str | None = Field(default=None)
    row_index: int | None = Field(default=None)
    page_number: int | None = Field(default=None)
    bounding_box_json: str | None = Field(default=None)
    title: str = Field(..., min_length=1)
    excerpt_or_reference: str = Field(...)
    source: str = Field(default="Uploaded Document")
    file_path: str | None = Field(default=None)
    content_hash: str | None = Field(default=None)
    version: int = Field(default=1, ge=1)
    document_type: str = Field(default="General")
    location: str | None = Field(default=None)
    uploaded_by: str = Field(default="Auditor")
    status: EvidenceStatusEnum = Field(default=EvidenceStatusEnum.UPLOADED)
    sample_ref: str | None = Field(default=None)
    test_execution_id: str | None = Field(default=None)
    reviewed_by: str | None = Field(default=None)
    review_notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def file(self) -> str | None:
        return self.file_path

    @property
    def hash(self) -> str | None:
        return self.content_hash

    @property
    def related_procedure(self) -> str | None:
        return self.procedure_id

    @property
    def related_test(self) -> str | None:
        return self.test_execution_id

    @property
    def related_finding(self) -> str | None:
        return self.finding_id

    @property
    def related_working_paper(self) -> str | None:
        return self.working_paper_id
