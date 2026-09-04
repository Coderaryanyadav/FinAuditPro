"""DTOs for Indian Statutory Compliance: CARO 2020 and Form 3CD Tax Audit."""

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.compliance_entities import (
    CAROApplicabilityEnum,
    CAROReportAnswerEnum,
    TaxAuditCategoryEnum,
    TaxAuditCheckResultEnum,
)


class BaseComplianceDTO(BaseModel):
    model_config = ConfigDict(frozen=True)


class ExecuteCAROProcedureDTO(BaseComplianceDTO):
    engagement_id: str
    clause_code: str
    clause_title: str
    applicability: CAROApplicabilityEnum = CAROApplicabilityEnum.APPLICABLE
    applicability_reason: str = ""
    question: str = ""
    procedure_text: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    finding_refs: list[str] = Field(default_factory=list)
    management_response: str = ""
    conclusion_text: str = ""
    report_answer: CAROReportAnswerEnum = CAROReportAnswerEnum.UNQUALIFIED


class ReviewCAROClauseDTO(BaseComplianceDTO):
    engagement_id: str
    clause_code: str
    decision: str = "APPROVE"  # APPROVE / REJECT
    reviewer_notes: str | None = None


class RunTaxAuditCheckDTO(BaseComplianceDTO):
    engagement_id: str
    clause_code: str
    category: TaxAuditCategoryEnum
    description: str
    input_source: str
    rule_logic: str
    system_result: TaxAuditCheckResultEnum = TaxAuditCheckResultEnum.COMPLIANT
    exception_amount_paise: int = 0
    evidence_ref: str | None = None


class ConcludeTaxAuditCheckDTO(BaseComplianceDTO):
    engagement_id: str
    check_id: str
    auditor_conclusion: TaxAuditCheckResultEnum
    exception_amount_paise: int = 0
    reviewer_notes: str | None = None
