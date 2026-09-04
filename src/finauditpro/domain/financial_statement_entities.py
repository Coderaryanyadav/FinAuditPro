"""Pure domain entities for Schedule III Financial Statements, Notes, Cash Flow, and Packaging."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class ScheduleIIISectionEnum(StrEnum):
    EQUITY_AND_LIABILITIES = "Equity and Liabilities"
    ASSETS = "Assets"
    INCOME = "Income"
    EXPENSES = "Expenses"


class ScheduleIIIDivisionEnum(StrEnum):
    DIVISION_I_AS = "Division I - AS"
    DIVISION_II_IND_AS = "Division II - Ind AS"


class DisclosureClassificationEnum(StrEnum):
    AUTOMATIC = "AUTOMATIC"
    SYSTEM_CHECKED = "SYSTEM-CHECKED"
    USER_REQUIRED = "USER-REQUIRED"
    MANUAL_REVIEW = "MANUAL REVIEW"
    NOT_SUPPORTED = "NOT SUPPORTED"


class FinancialStatementVersionEnum(StrEnum):
    DRAFT_V1 = "Draft V1"
    DRAFT_V2 = "Draft V2"
    REVIEWED_V3 = "Reviewed V3"
    FINAL_LOCKED_V4 = "Final V4"


class PackageStatusEnum(StrEnum):
    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    REVIEWED = "Reviewed"
    APPROVED = "Approved"
    FINAL = "Final"
    LOCKED = "Locked"


class CashFlowActivityTypeEnum(StrEnum):
    OPERATING = "Operating Activities"
    INVESTING = "Investing Activities"
    FINANCING = "Financing Activities"
    CASH_EQUIVALENT = "Cash and Cash Equivalents"


class BalanceSheetLineItem(DomainBaseModel):
    """Line item in Schedule III Balance Sheet."""

    line_code: str
    section: ScheduleIIISectionEnum
    category: str
    line_item: str
    current_period_paise: int = 0
    previous_period_paise: int = 0
    note_ref: str | None = None
    mapped_account_codes: list[str] = Field(default_factory=list)
    is_subtotal: bool = False
    is_heading: bool = False


class BalanceSheet(DomainBaseModel):
    """Schedule III Balance Sheet representation."""

    engagement_id: str
    as_at_date: str
    division: ScheduleIIIDivisionEnum = ScheduleIIIDivisionEnum.DIVISION_I_AS
    equity_and_liabilities_lines: list[BalanceSheetLineItem] = Field(default_factory=list)
    assets_lines: list[BalanceSheetLineItem] = Field(default_factory=list)
    total_equity_and_liabilities_paise: int = 0
    total_assets_paise: int = 0
    is_balanced: bool = False
    difference_paise: int = 0
    unmapped_accounts: list[str] = Field(default_factory=list)


class ProfitAndLossLineItem(DomainBaseModel):
    """Line item in Schedule III Statement of Profit & Loss."""

    line_code: str
    category: str
    line_item: str
    current_period_paise: int = 0
    previous_period_paise: int = 0
    note_ref: str | None = None
    mapped_account_codes: list[str] = Field(default_factory=list)
    is_subtotal: bool = False


class ProfitAndLossStatement(DomainBaseModel):
    """Schedule III Statement of Profit & Loss representation."""

    engagement_id: str
    for_period_ended: str
    revenue_lines: list[ProfitAndLossLineItem] = Field(default_factory=list)
    expense_lines: list[ProfitAndLossLineItem] = Field(default_factory=list)
    total_revenue_paise: int = 0
    total_expenses_paise: int = 0
    profit_before_tax_paise: int = 0
    tax_expense_paise: int = 0
    profit_after_tax_paise: int = 0


class StatementOfChangesInEquity(DomainBaseModel):
    """Statement of Changes in Equity / Reserves Reconciliation."""

    engagement_id: str
    opening_share_capital_paise: int = 0
    share_capital_changes_paise: int = 0
    closing_share_capital_paise: int = 0
    opening_reserves_surplus_paise: int = 0
    profit_for_the_year_paise: int = 0
    dividends_paid_paise: int = 0
    transfers_paise: int = 0
    closing_reserves_surplus_paise: int = 0
    total_closing_equity_paise: int = 0


class CashFlowLineItem(DomainBaseModel):
    """Line item in Cash Flow Statement."""

    description: str
    activity_type: CashFlowActivityTypeEnum
    amount_paise: int = 0
    is_inflow: bool = True
    note_ref: str | None = None


class CashFlowStatement(DomainBaseModel):
    """Statement of Cash Flows (Indirect Method as per AS 3 / Ind AS 7)."""

    engagement_id: str
    for_period_ended: str
    operating_activities: list[CashFlowLineItem] = Field(default_factory=list)
    investing_activities: list[CashFlowLineItem] = Field(default_factory=list)
    financing_activities: list[CashFlowLineItem] = Field(default_factory=list)
    net_cash_from_operating_paise: int = 0
    net_cash_from_investing_paise: int = 0
    net_cash_from_financing_paise: int = 0
    net_increase_in_cash_paise: int = 0
    opening_cash_and_equivalents_paise: int = 0
    closing_cash_and_equivalents_paise: int = 0
    financial_statement_cash_balance_paise: int = 0
    is_reconciled: bool = False
    reconciliation_difference_paise: int = 0


class FinancialStatementNote(DomainBaseModel):
    """Structured Note to Accounts supporting financial statement line items."""

    id: str = Field(default_factory=lambda: str(uuid4()))
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
    prepared_by: str = "Auditor"
    reviewed_by: str | None = None
    status: str = "Draft"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AccountingPolicy(DomainBaseModel):
    """Significant accounting policy disclosure."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str
    policy_code: str
    title: str
    category: str
    applicable_standard: str
    policy_text: str
    changes_text: str = "No changes during the reporting period."
    reviewed_by: str | None = None
    status: str = "Approved"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DataLineageNode(DomainBaseModel):
    """Deterministic lineage trace for any number on the financial statements."""

    fs_line_code: str
    fs_line_name: str
    note_ref: str | None = None
    note_title: str | None = None
    total_amount_paise: int = 0
    account_traces: list[dict[str, object]] = Field(default_factory=list)


class FinancialStatementPackage(DomainBaseModel):
    """Immutable/Versioned package containing full financial statements and notes."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str
    version: FinancialStatementVersionEnum = FinancialStatementVersionEnum.DRAFT_V1
    status: PackageStatusEnum = PackageStatusEnum.DRAFT
    balance_sheet: BalanceSheet
    profit_and_loss: ProfitAndLossStatement
    cash_flow: CashFlowStatement
    changes_in_equity: StatementOfChangesInEquity
    notes: list[FinancialStatementNote] = Field(default_factory=list)
    policies: list[AccountingPolicy] = Field(default_factory=list)
    data_hash: str = ""
    is_locked: bool = False
    is_stale: bool = False
    created_by: str = "Auditor"
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
