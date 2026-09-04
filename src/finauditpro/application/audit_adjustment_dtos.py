"""DTOs for Audit Adjusting Journal Entries (AJE) and Adjusted Trial Balance."""

from dataclasses import dataclass

from finauditpro.domain.audit_adjustment_entities import AJETypeEnum


@dataclass(frozen=True)
class CreateAJELineDTO:
    account_code: str
    account_name: str
    debit_paise: int = 0
    credit_paise: int = 0
    lead_schedule_ref: str | None = None
    narration: str | None = None


@dataclass(frozen=True)
class CreateAJEDTO:
    engagement_id: str
    aje_number: str
    entry_date: str
    title: str
    narration: str
    reason: str
    lines: list[CreateAJELineDTO]
    working_paper_ref: str | None = None
    aje_type: AJETypeEnum = AJETypeEnum.MANAGEMENT_ACCEPTED


@dataclass(frozen=True)
class UpdateAJEDTO:
    engagement_id: str
    entry_id: str
    title: str
    narration: str
    reason: str
    lines: list[CreateAJELineDTO]
    working_paper_ref: str | None = None
    aje_type: AJETypeEnum = AJETypeEnum.MANAGEMENT_ACCEPTED


@dataclass(frozen=True)
class SubmitAJEDTO:
    engagement_id: str
    entry_id: str


@dataclass(frozen=True)
class ReviewAJEDTO:
    engagement_id: str
    entry_id: str
    decision: str  # "APPROVE" or "REJECT"
    rejection_reason: str | None = None


@dataclass(frozen=True)
class ApplyAJEDTO:
    engagement_id: str
    entry_id: str


@dataclass(frozen=True)
class ReverseAJEDTO:
    engagement_id: str
    entry_id: str
    reversal_aje_number: str
    reason: str


@dataclass(frozen=True)
class AccountTraceDTO:
    account_code: str
    account_name: str
    schedule_iii_category: str
    schedule_iii_line_item: str
    lead_schedule_ref: str
    unadjusted_dr_paise: int
    unadjusted_cr_paise: int
    unadjusted_net_paise: int
    adjustment_dr_paise: int
    adjustment_cr_paise: int
    net_adjustment_paise: int
    adjusted_dr_paise: int
    adjusted_cr_paise: int
    adjusted_net_paise: int
    linked_ajes: list[dict[str, object]]


@dataclass(frozen=True)
class LeadScheduleTraceDTO:
    lead_schedule_ref: str
    lead_schedule_name: str
    category: str
    account_type: str
    total_unadjusted_paise: int
    total_adjustment_paise: int
    total_adjusted_paise: int
    accounts: list[AccountTraceDTO]

