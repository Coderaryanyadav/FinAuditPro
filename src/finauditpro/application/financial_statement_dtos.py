"""DTOs for Financial Statements, Notes, Cash Flow, and Packaging workflows."""

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.financial_statement_entities import (
    DisclosureClassificationEnum,
    FinancialStatementVersionEnum,
    ScheduleIIIDivisionEnum,
)


class BaseFSDTO(BaseModel):
    model_config = ConfigDict(frozen=True)


class GenerateFinancialStatementsDTO(BaseFSDTO):
    engagement_id: str
    as_at_date: str = "2026-03-31"
    for_period_ended: str = "2025-26"
    division: ScheduleIIIDivisionEnum = ScheduleIIIDivisionEnum.DIVISION_I_AS
    dataset_id: str | None = None


class SaveFinancialStatementPackageDTO(BaseFSDTO):
    engagement_id: str
    version: FinancialStatementVersionEnum = FinancialStatementVersionEnum.DRAFT_V1
    as_at_date: str = "2026-03-31"
    for_period_ended: str = "2025-26"
    dataset_id: str | None = None


class ReviewFinancialStatementPackageDTO(BaseFSDTO):
    engagement_id: str
    package_id: str
    decision: str = "APPROVE"  # APPROVE / REJECT
    reviewer_notes: str | None = None


class LockFinancialStatementPackageDTO(BaseFSDTO):
    engagement_id: str
    package_id: str


class CreateOrUpdateNoteDTO(BaseFSDTO):
    engagement_id: str
    package_id: str | None = None
    note_number: str
    title: str
    fs_reference: str
    source_type: str = "Mapped TB Accounts"
    disclosure_classification: DisclosureClassificationEnum = DisclosureClassificationEnum.AUTOMATIC
    amount_paise: int = 0
    details: list[dict[str, object]] = Field(default_factory=list)
    narrative: str = ""


class CreateOrUpdatePolicyDTO(BaseFSDTO):
    engagement_id: str
    policy_code: str
    title: str
    category: str
    applicable_standard: str
    policy_text: str
    changes_text: str = "No changes"


class GetDataLineageDTO(BaseFSDTO):
    engagement_id: str
    line_code: str
    dataset_id: str | None = None
