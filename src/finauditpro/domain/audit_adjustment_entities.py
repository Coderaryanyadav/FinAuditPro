"""Domain entities for Audit Adjustment Journal Entries (AJE), Adjusted Trial Balance, and Lead Schedule Rollups."""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.clock import utc_now
from finauditpro.domain.exceptions import ValidationError


class AJEStatusEnum(StrEnum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    APPLIED = "Applied"
    REJECTED = "Rejected"
    REVERSED = "Reversed"


class AJETypeEnum(StrEnum):
    MANAGEMENT_ACCEPTED = "Management Accepted"
    UNCORRECTED_PASSED = "Uncorrected / Passed Adjustment"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class AuditJournalLine(DomainBaseModel):
    """Line item of an Audit Adjusting Journal Entry with exact integer paise amounts."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    entry_id: str = Field(...)
    line_no: int = Field(..., ge=1)
    account_code: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    debit_paise: int = Field(default=0, ge=0)
    credit_paise: int = Field(default=0, ge=0)
    lead_schedule_ref: str | None = Field(default=None)
    narration: str | None = Field(default=None)


class AuditJournalEntry(DomainBaseModel):
    """Aggregate root representing a balanced Audit Adjusting Journal Entry (AJE)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    aje_number: str = Field(..., min_length=1)
    entry_date: str = Field(...)
    aje_type: AJETypeEnum = Field(default=AJETypeEnum.MANAGEMENT_ACCEPTED)
    status: AJEStatusEnum = Field(default=AJEStatusEnum.DRAFT)
    title: str = Field(..., min_length=1)
    narration: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    working_paper_ref: str | None = Field(default=None)
    total_debit_paise: int = Field(default=0, ge=0)
    total_credit_paise: int = Field(default=0, ge=0)
    prepared_by: str = Field(...)
    prepared_at: str = Field(default_factory=lambda: utc_now().isoformat())
    reviewed_by: str | None = Field(default=None)
    reviewed_at: str | None = Field(default=None)
    reversal_of_entry_id: str | None = Field(default=None)
    lines: list[AuditJournalLine] = Field(default_factory=list)

    def validate_double_entry(self) -> None:
        """Enforce strict server-side double-entry equality invariant (Debits == Credits > 0)."""
        if not self.lines or len(self.lines) < 2:
            raise ValidationError(
                f"AJE '{self.aje_number}' must have at least two journal lines (debit and credit)."
            )

        for line in self.lines:
            if line.debit_paise > 0 and line.credit_paise > 0:
                raise ValidationError(
                    f"Line {line.line_no} in AJE '{self.aje_number}' cannot have both debit (₹{line.debit_paise / 100:,.2f}) and credit (₹{line.credit_paise / 100:,.2f}) amounts."
                )
            if line.debit_paise == 0 and line.credit_paise == 0:
                raise ValidationError(
                    f"Line {line.line_no} in AJE '{self.aje_number}' must have a non-zero debit or credit amount."
                )

        tot_dr = sum(line.debit_paise for line in self.lines)
        tot_cr = sum(line.credit_paise for line in self.lines)

        if tot_dr <= 0:
            raise ValidationError(
                f"AJE '{self.aje_number}' total debit amount must be greater than zero."
            )

        if tot_dr != tot_cr:
            diff = abs(tot_dr - tot_cr)
            raise ValidationError(
                f"Double-Entry Violation in AJE '{self.aje_number}': Total Debits (₹{tot_dr / 100:,.2f}) "
                f"does not equal Total Credits (₹{tot_cr / 100:,.2f}). Imbalance: ₹{diff / 100:,.2f}."
            )

        self.total_debit_paise = tot_dr
        self.total_credit_paise = tot_cr

    def submit_for_review(self, actor: str) -> None:
        if self.status not in (AJEStatusEnum.DRAFT, AJEStatusEnum.REJECTED):
            raise ValidationError(
                f"Cannot submit AJE '{self.aje_number}' from status '{self.status}'."
            )
        self.validate_double_entry()
        self.status = AJEStatusEnum.SUBMITTED

    def approve(self, reviewer: str) -> None:
        if self.status != AJEStatusEnum.SUBMITTED:
            raise ValidationError(
                f"Cannot approve AJE '{self.aje_number}' because it is in status '{self.status}' (must be Submitted)."
            )
        self.validate_double_entry()
        self.status = AJEStatusEnum.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = utc_now().isoformat()

    def reject(self, reviewer: str, reason: str) -> None:
        if self.status != AJEStatusEnum.SUBMITTED:
            raise ValidationError(
                f"Cannot reject AJE '{self.aje_number}' in status '{self.status}'."
            )
        self.status = AJEStatusEnum.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = utc_now().isoformat()
        self.reason = f"{self.reason} | Rejected: {reason}"

    def apply(self, actor: str) -> None:
        if self.status != AJEStatusEnum.APPROVED:
            raise ValidationError(
                f"Cannot apply AJE '{self.aje_number}' with status '{self.status}' (must be Approved first)."
            )
        self.validate_double_entry()
        self.status = AJEStatusEnum.APPLIED

    def mark_reversed(self, reversal_entry_id: str) -> None:
        self.status = AJEStatusEnum.REVERSED


class AdjustedTrialBalanceLine(DomainBaseModel):
    """Line of the Adjusted Trial Balance combining unadjusted balances and approved/applied AJEs."""

    account_code: str
    account_name: str
    schedule_iii_category: str = ""
    schedule_iii_line_item: str = ""
    lead_schedule_ref: str = "WP-MISC"
    account_type: AccountTypeEnum = AccountTypeEnum.ASSET
    unadjusted_dr_paise: int = 0
    unadjusted_cr_paise: int = 0
    unadjusted_net_paise: int = 0
    adjustment_dr_paise: int = 0
    adjustment_cr_paise: int = 0
    net_adjustment_paise: int = 0
    adjusted_dr_paise: int = 0
    adjusted_cr_paise: int = 0
    adjusted_net_paise: int = 0
    linked_aje_numbers: list[str] = Field(default_factory=list)


class AdjustedTrialBalanceSummary(DomainBaseModel):
    """Summary of the complete Adjusted Trial Balance with mathematical balance invariants."""

    total_unadjusted_dr_paise: int = 0
    total_unadjusted_cr_paise: int = 0
    total_adjustment_dr_paise: int = 0
    total_adjustment_cr_paise: int = 0
    total_adjusted_dr_paise: int = 0
    total_adjusted_cr_paise: int = 0
    line_count: int = 0
    applied_aje_count: int = 0
    lines: list[AdjustedTrialBalanceLine] = Field(default_factory=list)

    @property
    def is_unadjusted_balanced(self) -> bool:
        return self.total_unadjusted_dr_paise == self.total_unadjusted_cr_paise

    @property
    def is_adjustments_balanced(self) -> bool:
        return self.total_adjustment_dr_paise == self.total_adjustment_cr_paise

    @property
    def is_adjusted_balanced(self) -> bool:
        return self.total_adjusted_dr_paise == self.total_adjusted_cr_paise

    @property
    def is_balanced(self) -> bool:
        return self.is_adjusted_balanced

    @property
    def is_fully_balanced(self) -> bool:
        return (
            self.is_unadjusted_balanced
            and self.is_adjustments_balanced
            and self.is_adjusted_balanced
        )


class LeadScheduleAccountLine(DomainBaseModel):
    account_code: str
    account_name: str
    schedule_iii_line_item: str
    unadjusted_balance_paise: int = 0
    adjustment_dr_paise: int = 0
    adjustment_cr_paise: int = 0
    net_adjustment_paise: int = 0
    adjusted_balance_paise: int = 0
    linked_aje_numbers: list[str] = Field(default_factory=list)


class LeadScheduleSummary(DomainBaseModel):
    """Lead Schedule summarizing all mapped accounts under a standard Schedule III audit head."""

    lead_schedule_ref: str
    lead_schedule_name: str
    category: str
    account_type: AccountTypeEnum
    unadjusted_balance_paise: int = 0
    adjustment_dr_paise: int = 0
    adjustment_cr_paise: int = 0
    net_adjustment_paise: int = 0
    adjusted_balance_paise: int = 0
    account_count: int = 0
    accounts: list[LeadScheduleAccountLine] = Field(default_factory=list)
