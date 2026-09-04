"""Domain entities for Schedule III Account Mapping, Taxonomies, and Lead Schedule Rollups."""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class MappingStatusEnum(StrEnum):
    UNMAPPED = "Unmapped"
    MAPPED = "Mapped"
    REVIEW_REQUIRED = "Review Required"
    LOCKED = "Locked"


class AccountTypeEnum(StrEnum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class ScheduleIIIHead(DomainBaseModel):
    category: str
    line_item: str
    account_type: AccountTypeEnum
    lead_schedule_ref: str
    description: str = ""


# Standard Schedule III (Division I / AS and Division II / Ind AS) Taxonomy Mapping
SCHEDULE_III_TAXONOMY: list[ScheduleIIIHead] = [
    # Equity & Liabilities
    ScheduleIIIHead(
        category="Share Capital",
        line_item="Equity Share Capital",
        account_type=AccountTypeEnum.EQUITY,
        lead_schedule_ref="WP-A1",
        description="Issued, subscribed and paid-up equity share capital",
    ),
    ScheduleIIIHead(
        category="Share Capital",
        line_item="Preference Share Capital",
        account_type=AccountTypeEnum.EQUITY,
        lead_schedule_ref="WP-A1",
        description="Preference share capital",
    ),
    ScheduleIIIHead(
        category="Reserves and Surplus",
        line_item="Retained Earnings / General Reserve",
        account_type=AccountTypeEnum.EQUITY,
        lead_schedule_ref="WP-A2",
        description="Capital reserves, securities premium, general reserves, surplus in P&L",
    ),
    ScheduleIIIHead(
        category="Long-Term Borrowings",
        line_item="Term Loans from Banks & FIs",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-B1",
        description="Secured and unsecured term borrowings",
    ),
    ScheduleIIIHead(
        category="Deferred Tax Liabilities (Net)",
        line_item="Deferred Tax Liabilities",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-B2",
        description="Timing differences on depreciation and statutory deductions",
    ),
    ScheduleIIIHead(
        category="Other Long-Term Liabilities",
        line_item="Trade Deposits & Retention Monies",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-B3",
        description="Security deposits and long-term payables",
    ),
    ScheduleIIIHead(
        category="Short-Term Borrowings",
        line_item="Working Capital Loans & Overdrafts",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-C1",
        description="Cash credit, overdrafts, and short-term bank facilities",
    ),
    ScheduleIIIHead(
        category="Trade Payables",
        line_item="Trade Payables - MSME",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-C2",
        description="Outstanding dues of Micro and Small Enterprises u/s 43B(h)",
    ),
    ScheduleIIIHead(
        category="Trade Payables",
        line_item="Trade Payables - Others",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-C2",
        description="Outstanding dues of creditors other than micro and small enterprises",
    ),
    ScheduleIIIHead(
        category="Other Current Liabilities",
        line_item="Statutory Dues & Advance from Customers",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-C3",
        description="GST, TDS, PF, ESI, and advances from customers",
    ),
    ScheduleIIIHead(
        category="Short-Term Provisions",
        line_item="Provision for Tax & Employee Benefits",
        account_type=AccountTypeEnum.LIABILITY,
        lead_schedule_ref="WP-C4",
        description="Income tax provisions, bonus, leave encashment provisions",
    ),
    # Non-Current Assets
    ScheduleIIIHead(
        category="Property, Plant and Equipment",
        line_item="Freehold & Leasehold Land",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-D1",
        description="Tangible land assets",
    ),
    ScheduleIIIHead(
        category="Property, Plant and Equipment",
        line_item="Buildings & Civil Structures",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-D1",
        description="Factory, office buildings, and premises",
    ),
    ScheduleIIIHead(
        category="Property, Plant and Equipment",
        line_item="Plant, Machinery & Equipment",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-D1",
        description="Manufacturing plant and electrical equipment",
    ),
    ScheduleIIIHead(
        category="Property, Plant and Equipment",
        line_item="Furniture, Fixtures & Office Equipment",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-D1",
        description="Office furniture, computers, servers, air conditioning",
    ),
    ScheduleIIIHead(
        category="Property, Plant and Equipment",
        line_item="Vehicles",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-D1",
        description="Motor cars, trucks, and transport equipment",
    ),
    ScheduleIIIHead(
        category="Capital Work-in-Progress (CWIP)",
        line_item="Capital Work-in-Progress",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-D2",
        description="Assets under construction/installation",
    ),
    ScheduleIIIHead(
        category="Intangible Assets",
        line_item="Software, Patents & Trademarks",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-D3",
        description="Acquired software licenses, goodwill, and patents",
    ),
    ScheduleIIIHead(
        category="Non-Current Investments",
        line_item="Investments in Subsidiaries & Bonds",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-E1",
        description="Long-term investments in equity shares, mutual funds, bonds",
    ),
    ScheduleIIIHead(
        category="Long-Term Loans and Advances",
        line_item="Security Deposits & Capital Advances",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-E2",
        description="Electricity deposits, rental deposits, capital advances",
    ),
    # Current Assets
    ScheduleIIIHead(
        category="Inventories",
        line_item="Raw Materials & Consumables",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-F1",
        description="Stock of raw materials and stores",
    ),
    ScheduleIIIHead(
        category="Inventories",
        line_item="Work-in-Progress",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-F1",
        description="Semi-finished goods under production",
    ),
    ScheduleIIIHead(
        category="Inventories",
        line_item="Finished Goods & Stock-in-Trade",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-F1",
        description="Finished goods ready for dispatch",
    ),
    ScheduleIIIHead(
        category="Trade Receivables",
        line_item="Trade Receivables - Undisputed Good",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-G1",
        description="Book debts and customer receivables considered good",
    ),
    ScheduleIIIHead(
        category="Cash and Cash Equivalents",
        line_item="Balances with Banks & Fixed Deposits",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-H1",
        description="Current account balances, flexi deposits, cash on hand",
    ),
    ScheduleIIIHead(
        category="Short-Term Loans and Advances",
        line_item="Prepaid Expenses & GST/TDS Balances",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-H2",
        description="GST input tax credit receivable, advance tax, prepaid insurance",
    ),
    ScheduleIIIHead(
        category="Other Current Assets",
        line_item="Interest Accrued & Claims",
        account_type=AccountTypeEnum.ASSET,
        lead_schedule_ref="WP-H3",
        description="Interest receivable and miscellaneous assets",
    ),
    # Revenue & Expenses (P&L)
    ScheduleIIIHead(
        category="Revenue from Operations",
        line_item="Sale of Products & Services",
        account_type=AccountTypeEnum.INCOME,
        lead_schedule_ref="WP-I1",
        description="Gross revenue from sale of manufactured/traded goods and services",
    ),
    ScheduleIIIHead(
        category="Other Income",
        line_item="Interest Income & Foreclosures",
        account_type=AccountTypeEnum.INCOME,
        lead_schedule_ref="WP-I2",
        description="Interest from fixed deposits, dividend income, profit on sale of assets",
    ),
    ScheduleIIIHead(
        category="Cost of Materials Consumed",
        line_item="Raw Material Consumption",
        account_type=AccountTypeEnum.EXPENSE,
        lead_schedule_ref="WP-J1",
        description="Direct material consumption in manufacturing",
    ),
    ScheduleIIIHead(
        category="Employee Benefits Expense",
        line_item="Salaries, Wages & Staff Welfare",
        account_type=AccountTypeEnum.EXPENSE,
        lead_schedule_ref="WP-K1",
        description="Staff salaries, director remuneration, PF contribution, gratuity",
    ),
    ScheduleIIIHead(
        category="Finance Costs",
        line_item="Interest Expense & Bank Charges",
        account_type=AccountTypeEnum.EXPENSE,
        lead_schedule_ref="WP-L1",
        description="Bank loan interest, processing fees, discount charges",
    ),
    ScheduleIIIHead(
        category="Depreciation and Amortization",
        line_item="Depreciation on PPE",
        account_type=AccountTypeEnum.EXPENSE,
        lead_schedule_ref="WP-M1",
        description="Schedule II depreciation and amortization charges",
    ),
    ScheduleIIIHead(
        category="Other Expenses",
        line_item="Manufacturing, Admin & Selling Expenses",
        account_type=AccountTypeEnum.EXPENSE,
        lead_schedule_ref="WP-N1",
        description="Power and fuel, freight, rent, rates and taxes, audit fees, sales promotion",
    ),
]


class AccountMapping(DomainBaseModel):
    """Account mapping associating a client ledger account with standard Schedule III classification."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    account_code: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    schedule_iii_category: str = Field(default="")
    schedule_iii_line_item: str = Field(default="")
    lead_schedule_ref: str = Field(default="WP-MISC")
    account_type: AccountTypeEnum = Field(default=AccountTypeEnum.ASSET)
    status: MappingStatusEnum = Field(default=MappingStatusEnum.UNMAPPED)
    is_material: bool = Field(default=True)
    is_new: bool = Field(default=False)
    mapped_by: str = Field(default="Auditor")
    mapped_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_by: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    notes: str | None = Field(default=None)

    def apply_mapping(
        self,
        category: str,
        line_item: str,
        lead_schedule_ref: str,
        account_type: AccountTypeEnum,
        actor: str,
        notes: str | None = None,
    ) -> None:
        self.schedule_iii_category = category
        self.schedule_iii_line_item = line_item
        self.lead_schedule_ref = lead_schedule_ref
        self.account_type = account_type
        self.status = MappingStatusEnum.MAPPED
        self.is_new = False
        self.updated_by = actor
        self.updated_at = utc_now().isoformat()
        if notes:
            self.notes = notes

    def lock_mapping(self, actor: str) -> None:
        self.status = MappingStatusEnum.LOCKED
        self.updated_by = actor
        self.updated_at = utc_now().isoformat()


class AccountMappingHistory(DomainBaseModel):
    """Immutable audit record for account mapping modifications."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    mapping_id: str = Field(...)
    changed_by: str = Field(...)
    changed_at: str = Field(default_factory=lambda: utc_now().isoformat())
    previous_category: str | None = Field(default=None)
    previous_line_item: str | None = Field(default=None)
    new_category: str = Field(...)
    new_line_item: str = Field(...)
    reason: str | None = Field(default=None)


class MappingValidationReport(DomainBaseModel):
    """Validation report verifying that trial balance accounts are adequately mapped before finalization."""

    total_accounts: int = Field(default=0)
    mapped_count: int = Field(default=0)
    unmapped_count: int = Field(default=0)
    material_unmapped_count: int = Field(default=0)
    new_accounts_count: int = Field(default=0)
    is_valid_for_finalization: bool = Field(default=False)
    validation_messages: list[str] = Field(default_factory=list)
