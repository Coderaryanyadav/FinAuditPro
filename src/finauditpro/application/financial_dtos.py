"""Data Transfer Objects (DTOs) for Financial Data and Analytics Services."""

from pydantic import BaseModel, Field

from finauditpro.domain.financial_entities import AnalyticsTypeEnum, DatasetTypeEnum


class InspectFileResultDTO(BaseModel):
    file_path: str
    headers: list[str]
    suggested_mappings: dict[str, str]
    preview_rows: list[dict[str, str]]


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
