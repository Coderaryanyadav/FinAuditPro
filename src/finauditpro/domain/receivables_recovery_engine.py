"""Pure domain entities and deterministic matching algorithms for Trade Receivables Subsequent Recovery Tie-Out."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class RecoveryStatusEnum(StrEnum):
    FULLY_RECOVERED = "Fully Recovered Post Balance Sheet Date"
    PARTIALLY_RECOVERED = "Partially Recovered"
    UNRECOVERED_OVERDUE = "Unrecovered Post Balance Sheet Date (ECL / Provision Required)"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class DebtorRecoveryRecord(DomainBaseModel):
    """Trade debtor balance matched against post-balance sheet bank receipts."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    debtor_code: str = Field(...)
    debtor_name: str = Field(...)
    balance_at_year_end_paise: int = Field(default=0, ge=0)
    subsequent_receipt_paise: int = Field(default=0, ge=0)
    unrecovered_balance_paise: int = Field(default=0, ge=0)
    recovery_status: RecoveryStatusEnum = Field(default=RecoveryStatusEnum.FULLY_RECOVERED)
    recovery_percentage: float = Field(default=100.0)
    ecl_provision_recommended_paise: int = Field(default=0, ge=0)
    audit_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class DebtorRecoverySummary:
    total_debtors_count: int
    fully_recovered_count: int
    partially_recovered_count: int
    unrecovered_count: int
    total_year_end_debtors_paise: int
    total_subsequent_receipts_paise: int
    total_unrecovered_paise: int
    records: list[DebtorRecoveryRecord]


class ReceivablesRecoveryEngine:
    """Deterministic validation engine for post-balance sheet debtor recoveries under SA 500 / SA 560."""

    @classmethod
    def tie_out_subsequent_receipts(
        cls,
        engagement_id: str,
        debtor_balances: list[dict[str, Any]],
        subsequent_receipts: list[dict[str, Any]],  # April-June bank ledger receipts
    ) -> DebtorRecoverySummary:
        """Tie out March 31st debtor balances against subsequent bank clearance entries."""
        # Index receipts by debtor_code
        receipt_map: dict[str, int] = {}
        for r in subsequent_receipts:
            code = r.get("debtor_code", "").strip().upper()
            amt = int(r.get("receipt_amount_paise", r.get("receipt_amount", 0) * 100))
            receipt_map[code] = receipt_map.get(code, 0) + amt

        records = []
        fully_cnt = 0
        part_cnt = 0
        unrec_cnt = 0
        tot_ye_paise = 0
        tot_rec_paise = 0
        tot_unrec_paise = 0

        for d in debtor_balances:
            code = d.get("debtor_code", "").strip().upper()
            name = d.get("debtor_name", "Unknown Debtor")
            ye_bal = int(d.get("balance_at_year_end_paise", d.get("balance", 0) * 100))
            tot_ye_paise += ye_bal

            rec_amt = receipt_map.get(code, 0)
            tot_rec_paise += min(ye_bal, rec_amt)

            unrec = max(0, ye_bal - rec_amt)
            tot_unrec_paise += unrec

            pct = round((rec_amt / ye_bal * 100.0), 2) if ye_bal > 0 else 100.0

            if unrec == 0:
                status = RecoveryStatusEnum.FULLY_RECOVERED
                prov = 0
                rem = f"100% subsequent recovery confirmed in bank records (₹{rec_amt/100:,.2f})."
                fully_cnt += 1
            elif rec_amt > 0:
                status = RecoveryStatusEnum.PARTIALLY_RECOVERED
                prov = int(unrec * 0.5)  # 50% prudent provision on overdue balance
                rem = f"Partially recovered {pct}%. Uncollected balance ₹{unrec/100:,.2f} requires provisioning."
                part_cnt += 1
            else:
                status = RecoveryStatusEnum.UNRECOVERED_OVERDUE
                prov = unrec  # 100% recommended provision
                rem = f"Zero post-year-end recovery. High credit default risk; evaluate full provision of ₹{unrec/100:,.2f}."
                unrec_cnt += 1

            records.append(
                DebtorRecoveryRecord(
                    engagement_id=engagement_id,
                    debtor_code=code,
                    debtor_name=name,
                    balance_at_year_end_paise=ye_bal,
                    subsequent_receipt_paise=rec_amt,
                    unrecovered_balance_paise=unrec,
                    recovery_status=status,
                    recovery_percentage=min(100.0, pct),
                    ecl_provision_recommended_paise=prov,
                    audit_remark=rem,
                )
            )

        return DebtorRecoverySummary(
            total_debtors_count=len(debtor_balances),
            fully_recovered_count=fully_cnt,
            partially_recovered_count=part_cnt,
            unrecovered_count=unrec_cnt,
            total_year_end_debtors_paise=tot_ye_paise,
            total_subsequent_receipts_paise=tot_rec_paise,
            total_unrecovered_paise=tot_unrec_paise,
            records=records,
        )
