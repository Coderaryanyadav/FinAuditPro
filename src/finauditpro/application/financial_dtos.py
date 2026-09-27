from typing import Any
from pydantic import BaseModel, Field

from finauditpro.domain.financial_entities import AnalyticsTypeEnum, DatasetTypeEnum, RowError


class InspectFileResultDTO(BaseModel):
    file_path: str
    headers: list[str]
    suggested_mappings: dict[str, str]
    preview_rows: list[dict[str, str]]


class ValidationRowPreviewDTO(BaseModel):
    row_no: int
    is_valid: bool
    data: dict[str, Any]
    errors: list[str] = Field(default_factory=list)


class ValidationPreviewDTO(BaseModel):
    file_path: str
    dataset_type: DatasetTypeEnum
    total_rows: int
    valid_rows_count: int
    error_count: int
    duplicate_count: int = 0
    total_debit_paise: int = 0
    total_credit_paise: int = 0
    is_balanced: bool = True
    discrepancy_paise: int = 0
    validation_passed: bool = True
    summary_message: str = ""
    errors: list[RowError] = Field(default_factory=list)
    sample_preview: list[ValidationRowPreviewDTO] = Field(default_factory=list)


class ImportDatasetDTO(BaseModel):
    engagement_id: str = Field(...)
    dataset_name: str = Field(..., min_length=1)
    dataset_type: DatasetTypeEnum = DatasetTypeEnum.GENERAL_LEDGER
    file_path: str = Field(...)
    column_mappings: dict[str, str] = Field(default_factory=dict)


class RunAnalyticsDTO(BaseModel):
    engagement_id: str = Field(...)
    dataset_id: str = Field(...)
    analysis_type: AnalyticsTypeEnum = Field(...)
    threshold: float | None = None


class FlaggedAnomalyDTO(BaseModel):
    id: str
    dataset_id: str
    row_index: int
    transaction_id: str | None
    date: str | None
    amount: float
    account_name: str | None
    rationale: str
    severity: str
    auditor_reviewed: bool
    auditor_notes: str | None


class CreateAuditWorkDTO(BaseModel):
    engagement_id: str = Field(...)
    dataset_id: str = Field(...)
    source: str = Field(default="Deterministic Analytics Engine")
    rule_or_analytic_id: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    severity: str = Field(default="Medium")
    audit_area: str = Field(default="General")
    assertion: str = Field(default="Accuracy")
    objective: str = Field(default="")
    implicated_rows: list[int] = Field(default_factory=list)
    computed_evidence: str = Field(default="")
    preparer: str = Field(default="Senior Auditor")


class RunReconciliationDTO(BaseModel):
    engagement_id: str = Field(...)
    dataset_id: str = Field(default="")
    reconciliation_type: str = Field(...)  # TB_BALANCE, SUBLEDGER_GL, BRS, GST_2B, FIXED_ASSETS
    as_of_date: str = Field(default="2026-03-31")
    data: dict[str, Any] = Field(default_factory=dict)

