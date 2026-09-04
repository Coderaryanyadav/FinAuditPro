"""Data Transfer Objects (DTOs) for Audit Matrix services."""

from pydantic import BaseModel, Field

from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    BenchmarkTypeEnum,
    FindingStatusEnum,
    ProcedureStatusEnum,
    RiskSeverityEnum,
)


class CalculateMaterialityDTO(BaseModel):
    engagement_id: str = Field(...)
    benchmark_type: BenchmarkTypeEnum = BenchmarkTypeEnum.REVENUE
    benchmark_amount: float = Field(..., ge=0.0)
    overall_percentage: float = Field(default=1.0, ge=0.1, le=10.0)
    performance_percentage: float = Field(default=75.0, ge=50.0, le=85.0)
    trivial_percentage: float = Field(default=5.0, ge=1.0, le=10.0)
    created_by: str = Field(default="Lead Auditor")


class CreateRiskDTO(BaseModel):
    engagement_id: str = Field(...)
    risk_code: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    title: str = Field(default="Audit Risk")
    assertions: list[AssertionEnum] | None = Field(default=None)
    assertion: AssertionEnum = AssertionEnum.COMPLETENESS
    inherent_risk: RiskSeverityEnum = RiskSeverityEnum.MEDIUM
    control_risk: RiskSeverityEnum = RiskSeverityEnum.MEDIUM
    severity: RiskSeverityEnum = RiskSeverityEnum.HIGH
    is_significant_risk: bool = Field(default=False)
    risk_response: str = Field(default="")


class CreateProcedureDTO(BaseModel):
    engagement_id: str = Field(...)
    risk_id: str | None = Field(default=None)
    linked_risk_ids: list[str] | None = Field(default=None)
    procedure_code: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    assertions: list[AssertionEnum] | None = Field(default=None)
    assertion: AssertionEnum = AssertionEnum.COMPLETENESS
    procedure_type: str = Field(default="Substantive Test")
    instructions: str = Field(default="")
    evidence_requirement: str = Field(default="")
    requires_evidence: bool = Field(default=True)


class UpdateProcedureStatusDTO(BaseModel):
    procedure_id: str = Field(...)
    status: ProcedureStatusEnum = Field(...)
    result_summary: str | None = Field(default=None)
    conclusion: str | None = Field(default=None)
    preparer: str | None = Field(default=None)
    reviewer: str | None = Field(default=None)


class CreateFindingDTO(BaseModel):
    engagement_id: str = Field(...)
    procedure_id: str | None = Field(default=None)
    risk_id: str | None = Field(default=None)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    category: str = Field(default="Substantive Exception")
    severity: RiskSeverityEnum = RiskSeverityEnum.HIGH
    monetary_amount: float = Field(default=0.0, ge=0.0)
    affected_account: str | None = Field(default=None)
    assertion: AssertionEnum = AssertionEnum.ACCURACY
    recommendation: str | None = Field(default=None)
    status: FindingStatusEnum = FindingStatusEnum.OPEN
    preparer: str = Field(default="Auditor")


class AttachEvidenceDTO(BaseModel):
    engagement_id: str = Field(...)
    finding_id: str | None = Field(default=None)
    procedure_id: str | None = Field(default=None)
    document_id: str | None = Field(default=None)
    dataset_id: str | None = Field(default=None)
    row_index: int | None = Field(default=None)
    page_number: int | None = Field(default=None)
    title: str = Field(..., min_length=1)
    excerpt_or_reference: str = Field(...)
