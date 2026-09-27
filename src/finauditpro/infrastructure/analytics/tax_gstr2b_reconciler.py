"""Tax & GSTR-2B 3-Way Reconciliation Engine with Section 16(2) & 17(5) ITC Eligibility Rules."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any


class MatchCategoryEnum(StrEnum):
    EXACT_MATCH = "Exact Match"
    TAX_MISMATCH = "Tax Amount Mismatch"
    MISSING_IN_2B = "Missing in GSTR-2B (Ineligible ITC)"
    MISSING_IN_BOOKS = "Missing in Books (Unclaimed Purchase)"


class ITCEligibilityEnum(StrEnum):
    ELIGIBLE = "Eligible"
    BLOCKED_SEC_17_5 = "Blocked Credit (Section 17(5))"
    INELIGIBLE_SUPPLIER_NON_FILING = "Ineligible (Supplier GSTR-3B Not Filed)"
    TIME_BARRED_SEC_16_4 = "Time-Barred (Section 16(4))"


@dataclass
class ReconciledInvoiceItem:
    invoice_number: str
    supplier_gstin: str
    supplier_name: str
    invoice_date: str
    books_tax_paise: int
    gstr2b_tax_paise: int
    variance_paise: int
    match_category: MatchCategoryEnum
    itc_eligibility: ITCEligibilityEnum
    notes: str = ""


@dataclass
class GSTR2BReconciliationSummary:
    total_books_records: int
    total_gstr2b_records: int
    exact_matches_count: int
    mismatch_count: int
    missing_in_2b_count: int
    missing_in_books_count: int
    total_books_itc_paise: int
    total_eligible_itc_paise: int
    total_blocked_itc_paise: int
    net_itc_at_risk_paise: int
    items: list[ReconciledInvoiceItem] = field(default_factory=list)


class TaxGSTR2BReconciler:
    """3-Way Reconciler comparing Purchase Register (Books) vs GSTR-2B vs GSTR-3B with Indian GST statutory rules."""

    @staticmethod
    def _is_blocked_under_17_5(description: str, hsn_sac: str = "") -> bool:
        """Detect blocked ITC under Section 17(5) of CGST Act (Motor Vehicles, Food, Health, etc.)."""
        d = description.lower()
        blocked_keywords = [
            "motor vehicle",
            "car",
            "cab",
            "food and beverage",
            "catering",
            "club membership",
            "health insurance",
            "gym",
            "personal consumption",
            "gift",
            "free sample",
        ]
        return any(k in d for k in blocked_keywords)

    @classmethod
    def reconcile(
        cls,
        books_purchases: list[dict[str, Any]],
        gstr2b_invoices: list[dict[str, Any]],
    ) -> GSTR2BReconciliationSummary:
        """Perform automated 3-way reconciliation across all invoices."""
        books_map = {
            f"{str(b.get('supplier_gstin', '')).strip().upper()}:{str(b.get('invoice_number', '')).strip().upper()}": b
            for b in books_purchases
        }
        gstr2b_map = {
            f"{str(g.get('supplier_gstin', '')).strip().upper()}:{str(g.get('invoice_number', '')).strip().upper()}": g
            for g in gstr2b_invoices
        }

        all_keys = set(books_map.keys()).union(set(gstr2b_map.keys()))

        reconciled_items: list[ReconciledInvoiceItem] = []
        exact_cnt = 0
        mismatch_cnt = 0
        missing_2b_cnt = 0
        missing_books_cnt = 0

        tot_books_itc = 0
        tot_eligible_itc = 0
        tot_blocked_itc = 0

        for k in sorted(all_keys):
            b_inv = books_map.get(k)
            g_inv = gstr2b_map.get(k)

            if b_inv and g_inv:
                b_tax = int(b_inv.get("tax_paise", 0) or int(Decimal(str(b_inv.get("tax_amount", 0))) * 100))
                g_tax = int(g_inv.get("tax_paise", 0) or int(Decimal(str(g_inv.get("tax_amount", 0))) * 100))
                diff = b_tax - g_tax
                tot_books_itc += b_tax

                desc = str(b_inv.get("description", ""))
                supplier_filed = g_inv.get("supplier_gstr3b_filed", True)

                # Determine ITC eligibility
                if cls._is_blocked_under_17_5(desc):
                    itc_status = ITCEligibilityEnum.BLOCKED_SEC_17_5
                    tot_blocked_itc += b_tax
                elif not supplier_filed:
                    itc_status = ITCEligibilityEnum.INELIGIBLE_SUPPLIER_NON_FILING
                    tot_blocked_itc += b_tax
                else:
                    itc_status = ITCEligibilityEnum.ELIGIBLE
                    tot_eligible_itc += min(b_tax, g_tax)

                if diff == 0:
                    cat = MatchCategoryEnum.EXACT_MATCH
                    exact_cnt += 1
                else:
                    cat = MatchCategoryEnum.TAX_MISMATCH
                    mismatch_cnt += 1

                reconciled_items.append(
                    ReconciledInvoiceItem(
                        invoice_number=str(b_inv.get("invoice_number", "")),
                        supplier_gstin=str(b_inv.get("supplier_gstin", "")),
                        supplier_name=str(b_inv.get("supplier_name", "")),
                        invoice_date=str(b_inv.get("invoice_date", "")),
                        books_tax_paise=b_tax,
                        gstr2b_tax_paise=g_tax,
                        variance_paise=diff,
                        match_category=cat,
                        itc_eligibility=itc_status,
                        notes="Matched across Books and GSTR-2B" if diff == 0 else f"Tax difference of ₹{abs(diff)/100:,.2f}",
                    )
                )

            elif b_inv and not g_inv:
                # Present in Books, Missing in 2B
                b_tax = int(b_inv.get("tax_paise", 0) or int(Decimal(str(b_inv.get("tax_amount", 0))) * 100))
                tot_books_itc += b_tax
                missing_2b_cnt += 1

                reconciled_items.append(
                    ReconciledInvoiceItem(
                        invoice_number=str(b_inv.get("invoice_number", "")),
                        supplier_gstin=str(b_inv.get("supplier_gstin", "")),
                        supplier_name=str(b_inv.get("supplier_name", "")),
                        invoice_date=str(b_inv.get("invoice_date", "")),
                        books_tax_paise=b_tax,
                        gstr2b_tax_paise=0,
                        variance_paise=b_tax,
                        match_category=MatchCategoryEnum.MISSING_IN_2B,
                        itc_eligibility=ITCEligibilityEnum.INELIGIBLE_SUPPLIER_NON_FILING,
                        notes="Invoice missing in GSTR-2B; ITC disallowed under Section 16(2)(aa).",
                    )
                )

            elif g_inv and not b_inv:
                # Present in GSTR-2B, Missing in Books
                g_tax = int(g_inv.get("tax_paise", 0) or int(Decimal(str(g_inv.get("tax_amount", 0))) * 100))
                missing_books_cnt += 1

                reconciled_items.append(
                    ReconciledInvoiceItem(
                        invoice_number=str(g_inv.get("invoice_number", "")),
                        supplier_gstin=str(g_inv.get("supplier_gstin", "")),
                        supplier_name=str(g_inv.get("supplier_name", "")),
                        invoice_date=str(g_inv.get("invoice_date", "")),
                        books_tax_paise=0,
                        gstr2b_tax_paise=g_tax,
                        variance_paise=-g_tax,
                        match_category=MatchCategoryEnum.MISSING_IN_BOOKS,
                        itc_eligibility=ITCEligibilityEnum.ELIGIBLE,
                        notes="Vendor reported in 2B but unbooked in company purchase register.",
                    )
                )

        net_risk = tot_books_itc - tot_eligible_itc

        return GSTR2BReconciliationSummary(
            total_books_records=len(books_purchases),
            total_gstr2b_records=len(gstr2b_invoices),
            exact_matches_count=exact_cnt,
            mismatch_count=mismatch_cnt,
            missing_in_2b_count=missing_2b_cnt,
            missing_in_books_count=missing_books_cnt,
            total_books_itc_paise=tot_books_itc,
            total_eligible_itc_paise=tot_eligible_itc,
            total_blocked_itc_paise=tot_blocked_itc,
            net_itc_at_risk_paise=net_risk,
            items=reconciled_items,
        )
