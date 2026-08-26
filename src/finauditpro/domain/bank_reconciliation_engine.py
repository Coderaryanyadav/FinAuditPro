"""Pure domain entities and deterministic audit verification for Bank Reconciliation Statements (BRS)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class BRSItemTypeEnum(StrEnum):
    UNPRESENTED_CHEQUE = "Cheque Issued but Not Presented"
    UNCREDITED_DEPOSIT = "Cheque / Cash Deposited but Not Credited"
    DIRECT_BANK_DEBIT = "Bank Charges / Direct Debit Not in Cash Book"
    DIRECT_BANK_CREDIT = "Direct Deposit / Interest Not in Cash Book"


class BRSExceptionSeverityEnum(StrEnum):
    NORMAL_TIMING_DIFFERENCE = "Normal Timing Difference"
    STALE_CHEQUE_REVERSAL = "Stale Cheque (>90 Days) - Reversal Required"
    DELAYED_BANKING_RISK = "Delayed Banking (>15 Days) - Teeming & Lading Risk"
    UNRECORDED_CASH_EXPENSE = "Unrecorded Bank Debit - Adjustment Required"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class BRSReconciledItem(DomainBaseModel):
    """Line item in Bank Reconciliation Statement evaluated for stale/delay anomalies."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    bank_account_number: str = Field(...)
    item_type: BRSItemTypeEnum = Field(...)
    reference_number: str = Field(default="")
    entry_date: str = Field(...)  # Cash book entry date
    clearance_date: str | None = Field(default=None)  # Bank clearance date (if cleared post-period)
    amount_paise: int = Field(default=0, ge=0)
    days_outstanding: int = Field(default=0, ge=0)
    exception_severity: BRSExceptionSeverityEnum = Field(default=BRSExceptionSeverityEnum.NORMAL_TIMING_DIFFERENCE)
    audit_recommendation: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class BRSAnalysisSummary:
    total_reconciling_items: int
    stale_cheques_count: int
    delayed_deposits_count: int
    total_reconciling_paise: int
    at_risk_amount_paise: int
    records: list[BRSReconciledItem]


class BankReconciliationEngine:
    """Deterministic validation engine for Bank Reconciliation Statements under SA 500 / SA 505."""

    @classmethod
    def audit_brs_statement(
        cls,
        engagement_id: str,
        as_of_date_str: str,  # e.g. "2026-03-31"
        items: list[dict[str, Any]],
    ) -> BRSAnalysisSummary:
        """Evaluate BRS reconciling items for statutory stale limits and delayed banking."""
        as_of_d = datetime.strptime(as_of_date_str, "%Y-%m-%d").date()
        records = []
        stale_cnt = 0
        delay_cnt = 0
        tot_paise = 0
        at_risk_paise = 0

        for itm in items:
            acc_no = itm.get("bank_account_number", "Primary Bank Account")
            i_type = itm.get("item_type", BRSItemTypeEnum.UNPRESENTED_CHEQUE)
            ref_no = itm.get("reference_number", "")
            entry_d_str = itm.get("entry_date", as_of_date_str)
            clear_d_str = itm.get("clearance_date")
            amt = int(itm.get("amount_paise", itm.get("amount", 0) * 100))
            tot_paise += amt

            entry_d = datetime.strptime(entry_d_str, "%Y-%m-%d").date()
            days_out = (as_of_d - entry_d).days

            severity = BRSExceptionSeverityEnum.NORMAL_TIMING_DIFFERENCE
            rec = "Reconciled timing difference."

            if i_type == BRSItemTypeEnum.UNPRESENTED_CHEQUE and days_out > 90:
                severity = BRSExceptionSeverityEnum.STALE_CHEQUE_REVERSAL
                rec = f"Cheque stale after 90 days under RBI guidelines. Reverse liability to creditor: ₹{amt/100:,.2f}."
                stale_cnt += 1
                at_risk_paise += amt
            elif i_type == BRSItemTypeEnum.UNCREDITED_DEPOSIT and days_out > 15:
                severity = BRSExceptionSeverityEnum.DELAYED_BANKING_RISK
                rec = f"Deposit pending for {days_out} days. Perform direct confirmation and inquiry for delayed banking."
                delay_cnt += 1
                at_risk_paise += amt
            elif i_type == BRSItemTypeEnum.DIRECT_BANK_DEBIT:
                severity = BRSExceptionSeverityEnum.UNRECORDED_CASH_EXPENSE
                rec = "Pass adjusting entry in cash book for unrecorded bank charges / auto-debit."
                at_risk_paise += amt

            records.append(
                BRSReconciledItem(
                    engagement_id=engagement_id,
                    bank_account_number=acc_no,
                    item_type=i_type,
                    reference_number=ref_no,
                    entry_date=entry_d_str,
                    clearance_date=clear_d_str,
                    amount_paise=amt,
                    days_outstanding=days_out,
                    exception_severity=severity,
                    audit_recommendation=rec,
                )
            )

        return BRSAnalysisSummary(
            total_reconciling_items=len(items),
            stale_cheques_count=stale_cnt,
            delayed_deposits_count=delay_cnt,
            total_reconciling_paise=tot_paise,
            at_risk_amount_paise=at_risk_paise,
            records=records,
        )
