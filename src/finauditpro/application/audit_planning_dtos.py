"""Data Transfer Objects (DTOs) for Audit Planning, Materiality, Risks, Procedures, Findings & Traceability."""

from dataclasses import dataclass, field
from typing import Any

from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    BenchmarkTypeEnum,
    FindingSourceEnum,
    FindingStatusEnum,
    ProcedureStatusEnum,
    RiskSeverityEnum,
)


@dataclass(frozen=True)
class SetMaterialityDTO:
    engagement_id: str
    benchmark_type: BenchmarkTypeEnum
    benchmark_amount_paise: int
    overall_percentage: float = 1.0
    performance_percentage: float = 75.0
    trivial_percentage: float = 5.0
    benchmark_source: str = "SA 320 Guidance (Editable Suggestion)"
    methodology_notes: str = ""
    created_by: str = "Lead Auditor"


@dataclass(frozen=True)
class CreateRiskDTO:
    engagement_id: str
    risk_code: str
    title: str
    category: str
    description: str
    assertions: list[AssertionEnum] = field(default_factory=lambda: [AssertionEnum.COMPLETENESS])
    inherent_risk: RiskSeverityEnum = RiskSeverityEnum.MEDIUM
    control_risk: RiskSeverityEnum = RiskSeverityEnum.MEDIUM
    is_significant_risk: bool = False
    planned_response: str = ""


@dataclass(frozen=True)
class CreateProcedureDTO:
    engagement_id: str
    procedure_code: str
    objective: str
    procedure_type: str = "Substantive Procedure"
    instructions: str = ""
    evidence_requirement: str = ""
    linked_risk_ids: list[str] = field(default_factory=list)
    assertions: list[AssertionEnum] = field(default_factory=lambda: [AssertionEnum.COMPLETENESS])
    preparer: str = "Auditor"


@dataclass(frozen=True)
class UpdateProcedureStatusDTO:
    procedure_id: str
    status: ProcedureStatusEnum
    result_summary: str | None = None
    conclusion: str | None = None
    reviewer: str | None = None


@dataclass(frozen=True)
class CreateFindingDTO:
    engagement_id: str
    title: str
    description: str
    category: str = "Substantive Audit Exception"
    severity: RiskSeverityEnum = RiskSeverityEnum.HIGH
    amount_paise: int | None = None
    affected_account: str | None = None
    assertion: AssertionEnum = AssertionEnum.ACCURACY
    procedure_id: str | None = None
    risk_id: str | None = None
    recommendation: str | None = None
    preparer: str = "Auditor"
    source: FindingSourceEnum = FindingSourceEnum.MANUAL
    is_ai_generated: bool = False
    prior_engagement_finding_id: str | None = None


@dataclass(frozen=True)
class UpdateFindingStatusDTO:
    finding_id: str
    new_status: FindingStatusEnum
    reviewer: str | None = None
    recommendation: str | None = None


@dataclass(frozen=True)
class AttachEvidenceDTO:
    engagement_id: str
    finding_id: str | None = None
    procedure_id: str | None = None
    document_id: str | None = None
    dataset_id: str | None = None
    page_number: int | None = None
    row_index: int | None = None
    bounding_box_json: str | None = None
    title: str = "Audit Evidence Link"
    excerpt_or_reference: str = ""


@dataclass
class TraceabilityGraphDTO:
    engagement_id: str
    finding_id: str | None
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
