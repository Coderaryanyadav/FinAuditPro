"""Pure domain entities and testing logic for Sales and Purchases Year-End Cut-Off (SA 315 / SA 330)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class CutOffPeriodEnum(StrEnum):
    PRE_YEAR_END = "Pre Year-End (-10 Days to March 31)"
    POST_YEAR_END = "Post Year-End (+10 Days from April 1)"


class CutOffExceptionTypeEnum(StrEnum):
    OK_CORRECT_PERIOD = "Correct Period Accounting"
    POST_YEAR_END_SALES_RETURN = "High-Value Post Year-End Sales Return (Window Dressing Risk)"
    PRE_YEAR_END_UNBILLED_DISPATCH = "Pre Year-End Dispatch Without Revenue Recognition"
    LATE_RECORDED_PURCHASE = "Goods Received Pre-Close Recorded in Next Fiscal Year"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class CutOffTestItem(DomainBaseModel):
    """Transaction item inspected under 10-day cut-off testing protocol."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    document_number: str = Field(...)
    document_date: str = Field(...)
    dispatch_or_receipt_date: str = Field(...)
    counterparty_name: str = Field(...)
    amount_paise: int = Field(default=0, ge=0)
    transaction_type: str = Field(...)  # Sales / Purchases / Returns
    period_classification: CutOffPeriodEnum = Field(...)
    exception_type: CutOffExceptionTypeEnum = Field(
        default=CutOffExceptionTypeEnum.OK_CORRECT_PERIOD
    )
    audit_finding_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class CutOffAnalysisSummary:
    total_inspected_items: int
    clean_items_count: int
    exception_count: int
    total_exception_value_paise: int
    records: list[CutOffTestItem]


class CutOffTestingEngine:
    """Deterministic validation engine for sales and purchase year-end cut-off."""

    @classmethod
    def analyze_cutoff_records(
        cls,
        engagement_id: str,
        year_end_date_str: str,  # e.g. "2026-03-31"
        transactions: list[dict[str, Any]],
    ) -> CutOffAnalysisSummary:
        """Inspect transactions within +/- 10 days of balance sheet closing date."""
        y_end = datetime.strptime(year_end_date_str, "%Y-%m-%d").date()
        records = []
        clean_cnt = 0
        exc_cnt = 0
        tot_exc_val = 0

        for t in transactions:
            doc_no = t.get("document_number", "")
            doc_d_str = t.get("document_date", year_end_date_str)
            disp_d_str = t.get("dispatch_or_receipt_date", doc_d_str)
            cp_name = t.get("counterparty_name", "Unknown Party")
            amt = int(t.get("amount_paise", t.get("amount", 0) * 100))
            txn_type = t.get("transaction_type", "Sales").capitalize()

            doc_d = datetime.strptime(doc_d_str, "%Y-%m-%d").date()
            disp_d = datetime.strptime(disp_d_str, "%Y-%m-%d").date()

            period = (
                CutOffPeriodEnum.PRE_YEAR_END if doc_d <= y_end else CutOffPeriodEnum.POST_YEAR_END
            )
            exc_type = CutOffExceptionTypeEnum.OK_CORRECT_PERIOD
            remark = "Proper accounting period cut-off."

            if (
                txn_type == "Returns"
                and period == CutOffPeriodEnum.POST_YEAR_END
                and (doc_d - y_end).days <= 15
            ):
                exc_type = CutOffExceptionTypeEnum.POST_YEAR_END_SALES_RETURN
                remark = f"Sales return of ₹{amt / 100:,.2f} booked {(doc_d - y_end).days} days post year-end. Possible inflation of revenue."
                exc_cnt += 1
                tot_exc_val += amt
            elif txn_type == "Sales" and disp_d <= y_end and doc_d > y_end:
                exc_type = CutOffExceptionTypeEnum.PRE_YEAR_END_UNBILLED_DISPATCH
                remark = f"Goods dispatched on {disp_d} (pre-year-end) but billed in next fiscal year ({doc_d})."
                exc_cnt += 1
                tot_exc_val += amt
            elif txn_type == "Purchases" and disp_d <= y_end and doc_d > y_end:
                exc_type = CutOffExceptionTypeEnum.LATE_RECORDED_PURCHASE
                remark = f"Materials received on {disp_d} (pre-year-end) but purchase invoice booked post-year-end."
                exc_cnt += 1
                tot_exc_val += amt
            else:
                clean_cnt += 1

            records.append(
                CutOffTestItem(
                    engagement_id=engagement_id,
                    document_number=doc_no,
                    document_date=doc_d_str,
                    dispatch_or_receipt_date=disp_d_str,
                    counterparty_name=cp_name,
                    amount_paise=amt,
                    transaction_type=txn_type,
                    period_classification=period,
                    exception_type=exc_type,
                    audit_finding_remark=remark,
                )
            )

        return CutOffAnalysisSummary(
            total_inspected_items=len(transactions),
            clean_items_count=clean_cnt,
            exception_count=exc_cnt,
            total_exception_value_paise=tot_exc_val,
            records=records,
        )
