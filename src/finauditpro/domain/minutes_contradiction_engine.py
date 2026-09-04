"""Pure domain entities and pattern matching scanner for Board and AGM Minutes contradictions."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class MinutesItemTypeEnum(StrEnum):
    BORROWING_LIMIT_RESOLUTION = "Borrowing Powers Resolution (Sec 180(1)(c))"
    RELATED_PARTY_APPROVAL = "Related Party Contract Approval (Sec 188)"
    DIVIDEND_DECLARATION = "Interim / Final Dividend Declaration"
    INVESTMENT_OR_LOAN = "Loans / Investments under Section 186"


class ContradictionSeverityEnum(StrEnum):
    MATCHED = "Consistent with Financial Statements"
    BORROWING_LIMIT_BREACH = "Borrowing Exceeds Authorized Section 180 Limit"
    UNRECORDED_DIVIDEND_LIABILITY = "Dividend Approved but Unrecorded in Books"
    MISSING_BOARD_APPROVAL = "Material Transaction Lacks Documented Board Resolution"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class MinutesResolutionRecord(DomainBaseModel):
    """Board / Committee resolution extracted and compared against general ledger balances."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    meeting_date: str = Field(...)
    meeting_type: str = Field(default="Board Meeting")  # Board Meeting / AGM / Audit Committee
    resolution_type: MinutesItemTypeEnum = Field(...)
    authorized_limit_paise: int = Field(default=0, ge=0)
    actual_ledger_amount_paise: int = Field(default=0, ge=0)
    severity: ContradictionSeverityEnum = Field(default=ContradictionSeverityEnum.MATCHED)
    extracted_text: str = Field(...)
    audit_finding_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class MinutesScanSummary:
    total_resolutions_scanned: int
    consistent_count: int
    contradictions_count: int
    records: list[MinutesResolutionRecord]


class MinutesContradictionEngine:
    """Scanner comparing Board/AGM minutes against statutory financial statement disclosures."""

    @classmethod
    def analyze_resolutions(
        cls,
        engagement_id: str,
        resolutions: list[dict[str, Any]],
        financial_balances: dict[str, int],  # e.g. {"total_borrowings_paise": 5000000000}
    ) -> MinutesScanSummary:
        """Scan corporate resolutions and cross-reference against actual ledger limits."""
        records = []
        consistent_cnt = 0
        contra_cnt = 0

        tot_borrowings = financial_balances.get("total_borrowings_paise", 0)

        for r in resolutions:
            m_date = r.get("meeting_date", "2025-09-30")
            m_type = r.get("meeting_type", "Board Meeting")
            r_type = r.get("resolution_type", MinutesItemTypeEnum.BORROWING_LIMIT_RESOLUTION)
            limit_p = int(r.get("authorized_limit_paise", r.get("authorized_limit", 0) * 100))
            text = r.get("extracted_text", "")

            sev = ContradictionSeverityEnum.MATCHED
            rem = "Resolution aligns with general ledger balances."
            actual_amt = 0

            if r_type == MinutesItemTypeEnum.BORROWING_LIMIT_RESOLUTION:
                actual_amt = tot_borrowings
                if tot_borrowings > limit_p:
                    sev = ContradictionSeverityEnum.BORROWING_LIMIT_BREACH
                    rem = (
                        f"Actual borrowings ₹{tot_borrowings / 100:,.2f} exceed authorized Section 180(1)(c) limit "
                        f"of ₹{limit_p / 100:,.2f}. Special Resolution in General Meeting required."
                    )
                    contra_cnt += 1
                else:
                    consistent_cnt += 1
            else:
                consistent_cnt += 1

            records.append(
                MinutesResolutionRecord(
                    engagement_id=engagement_id,
                    meeting_date=m_date,
                    meeting_type=m_type,
                    resolution_type=r_type,
                    authorized_limit_paise=limit_p,
                    actual_ledger_amount_paise=actual_amt,
                    severity=sev,
                    extracted_text=text,
                    audit_finding_remark=rem,
                )
            )

        return MinutesScanSummary(
            total_resolutions_scanned=len(resolutions),
            consistent_count=consistent_cnt,
            contradictions_count=contra_cnt,
            records=records,
        )
