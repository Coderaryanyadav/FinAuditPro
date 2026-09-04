"""Pure domain entities and algorithms for GSTR-2B vs Purchase Register 3-way matching and ITC verification."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class MatchStatusEnum(StrEnum):
    MATCHED = "Matched (Full ITC Eligible)"
    ITC_INELIGIBLE_SEC_17_5 = "Ineligible (Sec 17(5) Blocked Credit)"
    MISSING_IN_2B = "Missing in GSTR-2B (Vendor Non-Filing)"
    AMOUNT_MISMATCH = "Tax Amount Mismatch"
    GSTIN_MISMATCH = "GSTIN Mismatch"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class GSTReconciliationRecord(DomainBaseModel):
    """Reconciled purchase invoice against portal GSTR-2B return."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    invoice_number: str = Field(..., min_length=1)
    invoice_date: str = Field(...)
    vendor_name: str = Field(...)
    vendor_gstin: str = Field(...)
    books_taxable_paise: int = Field(default=0, ge=0)
    books_tax_paise: int = Field(default=0, ge=0)
    gstr2b_taxable_paise: int = Field(default=0, ge=0)
    gstr2b_tax_paise: int = Field(default=0, ge=0)
    match_status: MatchStatusEnum = Field(default=MatchStatusEnum.MATCHED)
    itc_available: bool = Field(default=True)
    discrepancy_rationale: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class GSTReconciliationSummary:
    total_vouchers: int
    matched_count: int
    mismatched_count: int
    ineligible_count: int
    total_books_itc_paise: int
    eligible_2b_itc_paise: int
    at_risk_itc_paise: int
    records: list[GSTReconciliationRecord]


class GSTReconciliationEngine:
    """Deterministic mathematical engine for GSTR-2B vs Books reconciliation."""

    @classmethod
    def match_purchase_register_with_2b(
        cls,
        engagement_id: str,
        books_invoices: list[dict[str, Any]],
        gstr2b_invoices: list[dict[str, Any]],
    ) -> GSTReconciliationSummary:
        """Execute deterministic 3-way invoice, GSTIN, and tax amount matching."""
        # Index GSTR-2B by (GSTIN, Normalized Invoice Number)
        b2_map = {}
        for g in gstr2b_invoices:
            k = (
                g.get("vendor_gstin", "").strip().upper(),
                g.get("invoice_number", "").strip().upper(),
            )
            b2_map[k] = g

        reconciled_records = []
        matched_cnt = 0
        mismatch_cnt = 0
        ineligible_cnt = 0
        tot_books_itc = 0
        eligible_2b_itc = 0
        at_risk_itc = 0

        for b in books_invoices:
            inv_no = b.get("invoice_number", "").strip().upper()
            gstin = b.get("vendor_gstin", "").strip().upper()
            v_name = b.get("vendor_name", "Unknown Vendor")
            inv_date = b.get("invoice_date", "2026-03-31")
            b_taxable = int(b.get("taxable_paise", b.get("taxable_amount", 0) * 100))
            b_tax = int(b.get("tax_paise", b.get("tax_amount", 0) * 100))
            tot_books_itc += b_tax

            is_blocked = b.get("is_sec_17_5_blocked", False)

            matched_2b = b2_map.get((gstin, inv_no))
            if is_blocked:
                status = MatchStatusEnum.ITC_INELIGIBLE_SEC_17_5
                rationale = "Blocked credit under Section 17(5) of CGST Act (e.g. motor vehicles, food & beverages)."
                itc_avail = False
                ineligible_cnt += 1
                at_risk_itc += b_tax
            elif not matched_2b:
                status = MatchStatusEnum.MISSING_IN_2B
                rationale = "Invoice not reflected in supplier's GSTR-1 / GSTR-2B. ITC restricted under Section 16(2)(aa)."
                itc_avail = False
                mismatch_cnt += 1
                at_risk_itc += b_tax
            else:
                g_tax = int(matched_2b.get("tax_paise", matched_2b.get("tax_amount", 0) * 100))
                if abs(b_tax - g_tax) > 100:  # > ₹1 tolerance
                    status = MatchStatusEnum.AMOUNT_MISMATCH
                    rationale = f"Books tax (₹{b_tax / 100:,.2f}) differs from 2B tax (₹{g_tax / 100:,.2f})."
                    itc_avail = False
                    mismatch_cnt += 1
                    at_risk_itc += abs(b_tax - g_tax)
                else:
                    status = MatchStatusEnum.MATCHED
                    rationale = "Full ITC match confirmed with GSTR-2B."
                    itc_avail = True
                    matched_cnt += 1
                    eligible_2b_itc += b_tax

            g_taxable_val = int(matched_2b.get("taxable_paise", 0)) if matched_2b else 0
            g_tax_val = int(matched_2b.get("tax_paise", 0)) if matched_2b else 0

            reconciled_records.append(
                GSTReconciliationRecord(
                    engagement_id=engagement_id,
                    invoice_number=inv_no,
                    invoice_date=inv_date,
                    vendor_name=v_name,
                    vendor_gstin=gstin,
                    books_taxable_paise=b_taxable,
                    books_tax_paise=b_tax,
                    gstr2b_taxable_paise=g_taxable_val,
                    gstr2b_tax_paise=g_tax_val,
                    match_status=status,
                    itc_available=itc_avail,
                    discrepancy_rationale=rationale,
                )
            )

        return GSTReconciliationSummary(
            total_vouchers=len(books_invoices),
            matched_count=matched_cnt,
            mismatched_count=mismatch_cnt,
            ineligible_count=ineligible_cnt,
            total_books_itc_paise=tot_books_itc,
            eligible_2b_itc_paise=eligible_2b_itc,
            at_risk_itc_paise=at_risk_itc,
            records=reconciled_records,
        )
