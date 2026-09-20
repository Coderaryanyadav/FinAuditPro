"""Data transfer objects for Unified Reconciliation Center."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MatchStatusEnum(StrEnum):
    MATCHED = "Matched"
    UNMATCHED = "Unmatched"
    POTENTIAL_MATCH = "Potential Match"
    NEEDS_REVIEW = "Needs Review"


class ReconciliationTabEnum(StrEnum):
    GST = "GST"
    BANK = "Bank"
    LEDGER = "Ledger"
    INVOICES = "Invoices"
    RECEIVABLES = "Receivables"
    PAYABLES = "Payables"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class ReconciliationSourceRecordDTO(DomainBaseModel):
    label: str = Field(..., min_length=1)
    reference: str = Field(default="")
    amount_paise: int = Field(default=0)
    details_json: str | None = Field(default=None)

    @property
    def amount_rupees(self) -> float:
        return self.amount_paise / 100.0


class ReconciliationItemDTO(DomainBaseModel):
    id: str = Field(..., min_length=1)
    tab: ReconciliationTabEnum = Field(...)
    item_key: str = Field(...)
    title: str = Field(...)
    match_status: MatchStatusEnum = Field(default=MatchStatusEnum.NEEDS_REVIEW)
    source_a: ReconciliationSourceRecordDTO = Field(...)
    source_b: ReconciliationSourceRecordDTO = Field(...)
    difference_paise: int = Field(default=0)
    discrepancy_reason: str = Field(default="")
    ai_explanation: str | None = Field(default=None)

    @property
    def difference_rupees(self) -> float:
        return self.difference_paise / 100.0


class ReconciliationSummaryDTO(DomainBaseModel):
    tab: ReconciliationTabEnum = Field(...)
    total_items: int = Field(default=0)
    matched_count: int = Field(default=0)
    unmatched_count: int = Field(default=0)
    potential_match_count: int = Field(default=0)
    needs_review_count: int = Field(default=0)
    items: list[ReconciliationItemDTO] = Field(default_factory=list)
