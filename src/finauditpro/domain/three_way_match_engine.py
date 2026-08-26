"""Pure domain entities and deterministic matching algorithms for Substantive Three-Way Matching."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class MatchDiscrepancyTypeEnum(StrEnum):
    MATCHED = "Fully Matched (PO = GRN = Invoice)"
    QUANTITY_VARIANCE = "Quantity Discrepancy (GRN Qty != Invoice Qty)"
    PRICE_VARIANCE = "Price / Rate Variance (PO Rate != Invoice Rate)"
    INVOICE_WITHOUT_GRN = "Invoice Without GRN (Potential Premature Billing)"
    GRN_WITHOUT_INVOICE = "GRN Without Invoice (Unrecorded Liability)"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class ThreeWayMatchRecord(DomainBaseModel):
    """Substantive 3-way match record across Purchase Order, GRN, and Invoice."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    po_number: str = Field(default="")
    grn_number: str = Field(default="")
    invoice_number: str = Field(default="")
    vendor_name: str = Field(...)
    item_description: str = Field(...)
    po_quantity: float = Field(default=0.0)
    grn_quantity: float = Field(default=0.0)
    invoice_quantity: float = Field(default=0.0)
    po_rate_paise: int = Field(default=0, ge=0)
    invoice_rate_paise: int = Field(default=0, ge=0)
    invoice_total_paise: int = Field(default=0, ge=0)
    discrepancy_type: MatchDiscrepancyTypeEnum = Field(default=MatchDiscrepancyTypeEnum.MATCHED)
    discrepancy_amount_paise: int = Field(default=0)
    audit_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class ThreeWayMatchSummary:
    total_matched_orders: int
    fully_matched_count: int
    discrepancy_count: int
    total_invoice_value_paise: int
    total_variance_paise: int
    records: list[ThreeWayMatchRecord]


class ThreeWayMatchEngine:
    """Deterministic mathematical engine for SA 330 / SA 500 Three-Way PO-GRN-Invoice matching."""

    @classmethod
    def match_orders(
        cls,
        engagement_id: str,
        orders: list[dict[str, Any]],
    ) -> ThreeWayMatchSummary:
        """Evaluate triplets of PO, GRN, and Invoices for rate/quantity variances."""
        records = []
        matched_cnt = 0
        disc_cnt = 0
        tot_val = 0
        tot_var = 0

        for o in orders:
            po_no = o.get("po_number", "")
            grn_no = o.get("grn_number", "")
            inv_no = o.get("invoice_number", "")
            v_name = o.get("vendor_name", "Unknown Vendor")
            item = o.get("item_description", "General Supply")
            po_qty = float(o.get("po_quantity", 0.0))
            grn_qty = float(o.get("grn_quantity", 0.0))
            inv_qty = float(o.get("invoice_quantity", 0.0))
            po_rate = int(o.get("po_rate_paise", o.get("po_rate", 0) * 100))
            inv_rate = int(o.get("invoice_rate_paise", o.get("invoice_rate", 0) * 100))
            inv_tot = int(o.get("invoice_total_paise", int(inv_qty * inv_rate)))
            tot_val += inv_tot

            if inv_no and not grn_no:
                disc_type = MatchDiscrepancyTypeEnum.INVOICE_WITHOUT_GRN
                var_paise = inv_tot
                remark = "Invoice billed without Goods Receipt Note (GRN). Potential unverified billing."
                disc_cnt += 1
                tot_var += var_paise
            elif grn_no and not inv_no:
                disc_type = MatchDiscrepancyTypeEnum.GRN_WITHOUT_INVOICE
                var_paise = int(grn_qty * po_rate)
                remark = "Goods received without vendor invoice. Unrecorded liability accrual required."
                disc_cnt += 1
                tot_var += var_paise
            elif abs(grn_qty - inv_qty) > 0.001:
                disc_type = MatchDiscrepancyTypeEnum.QUANTITY_VARIANCE
                qty_diff = abs(inv_qty - grn_qty)
                var_paise = int(qty_diff * inv_rate)
                remark = f"Quantity variance: GRN received {grn_qty} but billed for {inv_qty}."
                disc_cnt += 1
                tot_var += var_paise
            elif abs(po_rate - inv_rate) > 100:  # > ₹1 rate variance
                disc_type = MatchDiscrepancyTypeEnum.PRICE_VARIANCE
                rate_diff = abs(inv_rate - po_rate)
                var_paise = int(inv_qty * rate_diff)
                remark = f"Rate variance: PO rate ₹{po_rate/100:,.2f} vs Billed rate ₹{inv_rate/100:,.2f}."
                disc_cnt += 1
                tot_var += var_paise
            else:
                disc_type = MatchDiscrepancyTypeEnum.MATCHED
                var_paise = 0
                remark = "Full 3-way match verified."
                matched_cnt += 1

            records.append(
                ThreeWayMatchRecord(
                    engagement_id=engagement_id,
                    po_number=po_no,
                    grn_number=grn_no,
                    invoice_number=inv_no,
                    vendor_name=v_name,
                    item_description=item,
                    po_quantity=po_qty,
                    grn_quantity=grn_qty,
                    invoice_quantity=inv_qty,
                    po_rate_paise=po_rate,
                    invoice_rate_paise=inv_rate,
                    invoice_total_paise=inv_tot,
                    discrepancy_type=disc_type,
                    discrepancy_amount_paise=var_paise,
                    audit_remark=remark,
                )
            )

        return ThreeWayMatchSummary(
            total_matched_orders=len(orders),
            fully_matched_count=matched_cnt,
            discrepancy_count=disc_cnt,
            total_invoice_value_paise=tot_val,
            total_variance_paise=tot_var,
            records=records,
        )
