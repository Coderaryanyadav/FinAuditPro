"""Domain entities for Financial Data Import, Normalization, Deterministic Analytics, and Finding Promotion.

Design note: FinancialRecord uses Python float for debit/credit/amount because it holds
raw imported data before normalisation. LedgerEntry, TrialBalanceLine, and BankTransaction
use int paise (100 paise = ₹1) for all normalised financial calculations — this is the
authoritative representation for audit analytics and reporting.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now
from finauditpro.domain.value_objects import Money


class DatasetTypeEnum(StrEnum):
    GENERAL_LEDGER = "General Ledger"
    TRIAL_BALANCE = "Trial Balance"
    JOURNAL_ENTRIES = "Journal Entries"
    SALES_REGISTER = "Sales Register"
    PURCHASE_REGISTER = "Purchase Register"
    BANK_STATEMENT = "Bank Statement"
    VENDOR_MASTER = "Vendor Master"
    EXPENSE_REGISTER = "Expense Register"
    FIXED_ASSET_REGISTER = "Fixed Asset Register"


class AnalyticsTypeEnum(StrEnum):
    DUPLICATE_DETECTION = "Duplicate Detection"
    HIGH_VALUE_ANOMALY = "High-Value Transaction Anomaly"
    ROUND_NUMBER_CHECK = "Round Number Anomaly"
    WEEKEND_POSTING_CHECK = "Weekend Posting Anomaly"
    SEQUENCE_GAP_CHECK = "Sequence Gap Anomaly"
    PERIOD_VARIANCE_ANALYSIS = "Period Variance Analysis"
    RATIO_ANALYSIS = "Schedule III Statutory Ratios & Variance"
    SCHEDULE_III_DISCLOSURES = "Schedule III Division II Disclosures Check"


class DatasetStatusEnum(StrEnum):
    UPLOADED = "Uploaded"
    MAPPED = "Mapped"
    VALIDATING = "Validating"
    IMPORTED = "Imported"
    FAILED = "Failed"


class ExceptionStatusEnum(StrEnum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    ACCEPTED = "Accepted"
    DISMISSED = "Dismissed"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class FinancialRecord(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_id: str = Field(...)
    row_index: int = Field(..., ge=0)
    transaction_id: str | None = Field(default=None)
    date: str | None = Field(default=None)
    account_code: str | None = Field(default=None)
    account_name: str | None = Field(default=None)
    debit: float = Field(default=0.0)
    credit: float = Field(default=0.0)
    amount: float = Field(default=0.0)
    narration: str | None = Field(default=None)
    counterparty_name: str | None = Field(default=None)
    counterparty_gstin: str | None = Field(default=None)
    invoice_number: str | None = Field(default=None)
    extra_fields: dict[str, str] = Field(default_factory=dict)


class AnalyticsResult(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    dataset_id: str = Field(...)
    analysis_type: AnalyticsTypeEnum = Field(...)
    parameters_json: str = Field(default="{}")
    anomaly_count: int = Field(default=0, ge=0)
    summary: str = Field(...)
    reproducible_explanation: str = Field(...)
    created_at: datetime = Field(default_factory=utc_now)


class FlaggedAnomaly(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    analytics_result_id: str = Field(...)
    dataset_id: str = Field(...)
    row_index: int = Field(..., ge=0)
    transaction_id: str | None = Field(default=None)
    date: str | None = Field(default=None)
    amount: float = Field(default=0.0)
    account_name: str | None = Field(default=None)
    rationale: str = Field(...)
    severity: str = Field(default="Medium")
    auditor_reviewed: bool = Field(default=False)
    auditor_notes: str | None = Field(default=None)


class RowError(DomainBaseModel):
    row_no: int = Field(..., ge=1)
    column_name: str = Field(...)
    raw_value: str = Field(...)
    error_reason: str = Field(...)


class FinancialDataset(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    dataset_name: str = Field(..., min_length=1, max_length=255)
    dataset_type: DatasetTypeEnum = Field(default=DatasetTypeEnum.GENERAL_LEDGER)
    filename: str = Field(default="")
    content_hash: str = Field(default="0" * 64)
    stored_path: str = Field(default="")
    status: DatasetStatusEnum = Field(default=DatasetStatusEnum.IMPORTED)
    total_rows: int = Field(default=0, ge=0)
    row_count: int = Field(default=0, ge=0)
    error_rows: int = Field(default=0, ge=0)
    column_mappings: dict[str, str] = Field(default_factory=dict)
    errors: list[RowError] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def model_post_init(self, __context: Any) -> None:
        if not self.filename and self.dataset_name:
            self.filename = self.dataset_name
        if not self.stored_path and hasattr(self, "file_path_raw"):
            self.stored_path = self.file_path_raw

    @property
    def file_path(self) -> str:
        return self.stored_path or self.filename

    @property
    def valid_rows(self) -> int:
        return self.row_count

    @valid_rows.setter
    def valid_rows(self, value: int) -> None:
        self.row_count = value


class LedgerEntry(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_id: str = Field(...)
    source_row_no: int = Field(..., ge=1)
    entry_date: str | None = Field(default=None)  # YYYY-MM-DD
    voucher_type: str | None = Field(default=None)
    voucher_number: str | None = Field(default=None)
    account_code: str | None = Field(default=None)
    account_name: str | None = Field(default=None)
    debit_paise: int = Field(default=0, ge=0)
    credit_paise: int = Field(default=0, ge=0)
    narration: str | None = Field(default=None)
    reference: str | None = Field(default=None)
    created_by_raw: str | None = Field(default=None)
    raw_values: dict[str, str] = Field(default_factory=dict)

    @property
    def debit_money(self) -> Money:
        return Money(paise=self.debit_paise)

    @property
    def credit_money(self) -> Money:
        return Money(paise=self.credit_paise)


class TrialBalanceSummary(DomainBaseModel):
    total_opening_dr_paise: int = Field(default=0)
    total_opening_cr_paise: int = Field(default=0)
    total_debit_paise: int = Field(default=0)
    total_credit_paise: int = Field(default=0)
    total_closing_dr_paise: int = Field(default=0)
    total_closing_cr_paise: int = Field(default=0)

    @property
    def is_opening_balanced(self) -> bool:
        return self.total_opening_dr_paise == self.total_opening_cr_paise

    @property
    def is_period_balanced(self) -> bool:
        return self.total_debit_paise == self.total_credit_paise

    @property
    def is_closing_balanced(self) -> bool:
        return self.total_closing_dr_paise == self.total_closing_cr_paise

    @property
    def is_balanced(self) -> bool:
        return self.is_opening_balanced and self.is_period_balanced and self.is_closing_balanced

    @property
    def opening_discrepancy_paise(self) -> int:
        return self.total_opening_dr_paise - self.total_opening_cr_paise

    @property
    def period_discrepancy_paise(self) -> int:
        return self.total_debit_paise - self.total_credit_paise

    @property
    def closing_discrepancy_paise(self) -> int:
        return self.total_closing_dr_paise - self.total_closing_cr_paise


class TrialBalanceLine(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_id: str = Field(...)
    source_row_no: int = Field(..., ge=1)
    account_code: str | None = Field(default=None)
    account_name: str = Field(...)
    account_type: str | None = Field(default=None)
    opening_dr_paise: int = Field(default=0, ge=0)
    opening_cr_paise: int = Field(default=0, ge=0)
    debit_paise: int = Field(default=0, ge=0)
    credit_paise: int = Field(default=0, ge=0)
    closing_dr_paise: int = Field(default=0, ge=0)
    closing_cr_paise: int = Field(default=0, ge=0)
    raw_values: dict[str, str] = Field(default_factory=dict)


class BankTransaction(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_id: str = Field(...)
    source_row_no: int = Field(..., ge=1)
    txn_date: str | None = Field(default=None)
    value_date: str | None = Field(default=None)
    txn_id: str | None = Field(default=None)
    description: str = Field(...)
    debit_paise: int = Field(default=0, ge=0)
    credit_paise: int = Field(default=0, ge=0)
    balance_paise: int = Field(default=0)
    reference: str | None = Field(default=None)
    raw_values: dict[str, str] = Field(default_factory=dict)


class ExceptionItem(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    analysis_run_id: str = Field(...)
    dataset_id: str = Field(...)
    analytic_id: str = Field(...)
    severity: str = Field(default="Medium")
    title: str = Field(...)
    description: str = Field(...)
    implicated_rows: list[int] = Field(default_factory=list)
    computed_evidence: str = Field(...)
    status: ExceptionStatusEnum = Field(default=ExceptionStatusEnum.OPEN)
    reviewer: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Finding(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    title: str = Field(..., min_length=1)
    description: str = Field(...)
    category: str = Field(default="Substantive Audit Exception")
    severity: str = Field(default="High")
    amount_paise: int = Field(default=0, ge=0)
    affected_account: str | None = Field(default=None)
    source: str = Field(default="Deterministic Analytics Engine")
    ai_generated: bool = Field(default=False)  # Always False for Milestone 3
    status: str = Field(default="Open")
    preparer: str | None = Field(default="Senior Auditor")
    reviewer: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
