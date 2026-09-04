"""Application DTOs for Core Audit Engine workflows: Testing, Exceptions, Misstatements, and Quality Gates."""

from pydantic import BaseModel, ConfigDict

from finauditpro.domain.audit_execution_entities import (
    AuditTestOutcomeEnum,
    ExceptionStatusEnum,
    MisstatementTypeEnum,
    ProcedureConclusionEnum,
)


class CoreAuditBaseDTO(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)


class ExecuteSampleItemTestDTO(CoreAuditBaseDTO):
    procedure_id: str
    item_identifier: str
    sample_plan_id: str | None = None
    account_code: str | None = None
    expected_value_paise: int = 0
    actual_value_paise: int = 0
    test_result: AuditTestOutcomeEnum = AuditTestOutcomeEnum.PASS
    explanation: str = ""
    evidence_ref: str | None = None


class LogAuditExceptionDTO(CoreAuditBaseDTO):
    engagement_id: str
    procedure_id: str
    exception_code: str
    title: str
    description: str
    sample_item_id: str | None = None
    amount_paise: int = 0
    root_cause: str = ""
    evidence_id: str | None = None


class ResolveAuditExceptionDTO(CoreAuditBaseDTO):
    engagement_id: str
    exception_id: str
    management_response: str
    resolution: str
    is_resolved: bool = True
    status: ExceptionStatusEnum = ExceptionStatusEnum.RESOLVED


class CreateMisstatementDTO(CoreAuditBaseDTO):
    engagement_id: str
    account_code: str
    amount_paise: int
    account_name: str = ""
    schedule_iii_category: str = ""
    exception_id: str | None = None
    procedure_id: str | None = None
    misstatement_type: MisstatementTypeEnum = MisstatementTypeEnum.FACTUAL
    rationale: str = ""


class LinkMisstatementToAJEDTO(CoreAuditBaseDTO):
    engagement_id: str
    misstatement_id: str
    aje_id: str
    aje_number: str


class EvaluateProcedureConclusionDTO(CoreAuditBaseDTO):
    engagement_id: str
    procedure_id: str
    conclusion: ProcedureConclusionEnum
    result_summary: str
    override_reason: str | None = None


class GenerateAssertionCoverageDTO(CoreAuditBaseDTO):
    engagement_id: str


class CalculateAuditCompletenessDTO(CoreAuditBaseDTO):
    engagement_id: str
