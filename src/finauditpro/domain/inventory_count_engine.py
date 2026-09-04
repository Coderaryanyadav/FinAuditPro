"""Pure domain entities and testing algorithms for Physical Inventory Observation & Count Reconciliation (SA 501)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class InventoryDiscrepancyTypeEnum(StrEnum):
    MATCHED = "Count Confirmed with Book Ledger"
    PHYSICAL_SHORTAGE = "Physical Shortage (Book Qty > Physical Count)"
    PHYSICAL_EXCESS = "Physical Excess (Physical Count > Book Qty)"
    DAMAGED_OR_OBSOLETE = "Damaged / Obsolete Stock (NRV Impairment Required)"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class InventoryCountItem(DomainBaseModel):
    """Inventory item inspected during year-end physical inventory observation (SA 501)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    item_code: str = Field(...)
    item_description: str = Field(...)
    location: str = Field(...)
    book_quantity: float = Field(default=0.0, ge=0.0)
    physical_count_quantity: float = Field(default=0.0, ge=0.0)
    unit_cost_paise: int = Field(default=0, ge=0)
    discrepancy_type: InventoryDiscrepancyTypeEnum = Field(
        default=InventoryDiscrepancyTypeEnum.MATCHED
    )
    discrepancy_value_paise: int = Field(default=0)
    is_nrv_lower_than_cost: bool = Field(default=False)
    audit_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class InventoryObservationSummary:
    total_items_counted: int
    matched_items_count: int
    shortage_items_count: int
    excess_items_count: int
    obsolete_items_count: int
    total_shortage_value_paise: int
    records: list[InventoryCountItem]


class InventoryCountEngine:
    """Deterministic validation engine for physical inventory observation and book reconciliation under SA 501."""

    @classmethod
    def reconcile_physical_counts(
        cls,
        engagement_id: str,
        count_sheets: list[dict[str, Any]],
    ) -> InventoryObservationSummary:
        """Reconcile physical test counts against client perpetual inventory records."""
        records = []
        matched_cnt = 0
        shortage_cnt = 0
        excess_cnt = 0
        obsolete_cnt = 0
        tot_shortage_val = 0

        for c in count_sheets:
            code = c.get("item_code", "")
            desc = c.get("item_description", "General Stock Item")
            loc = c.get("location", "Main Warehouse")
            book_qty = float(c.get("book_quantity", 0.0))
            phys_qty = float(c.get("physical_count_quantity", 0.0))
            cost = int(c.get("unit_cost_paise", c.get("unit_cost", 0) * 100))
            is_damaged = c.get("is_damaged_or_obsolete", False)
            is_nrv_low = c.get("is_nrv_lower_than_cost", False)

            qty_diff = phys_qty - book_qty
            disc_type = InventoryDiscrepancyTypeEnum.MATCHED
            disc_val = 0
            remark = "Physical count confirmed against perpetual records."

            if is_damaged or is_nrv_low:
                disc_type = InventoryDiscrepancyTypeEnum.DAMAGED_OR_OBSOLETE
                disc_val = int(phys_qty * cost)
                remark = "Damaged / slow-moving stock identified. Verify AS 2 / Ind AS 2 lower of cost or NRV valuation."
                obsolete_cnt += 1
            elif qty_diff < -0.001:
                disc_type = InventoryDiscrepancyTypeEnum.PHYSICAL_SHORTAGE
                disc_val = int(abs(qty_diff) * cost)
                remark = f"Physical shortage of {abs(qty_diff)} units (Book: {book_qty}, Count: {phys_qty}). Investigate pilferage or unrecorded issue."
                shortage_cnt += 1
                tot_shortage_val += disc_val
            elif qty_diff > 0.001:
                disc_type = InventoryDiscrepancyTypeEnum.PHYSICAL_EXCESS
                disc_val = int(qty_diff * cost)
                remark = f"Physical excess of {qty_diff} units. Investigate unrecorded receipt or returns."
                excess_cnt += 1
            else:
                matched_cnt += 1

            records.append(
                InventoryCountItem(
                    engagement_id=engagement_id,
                    item_code=code,
                    item_description=desc,
                    location=loc,
                    book_quantity=book_qty,
                    physical_count_quantity=phys_qty,
                    unit_cost_paise=cost,
                    discrepancy_type=disc_type,
                    discrepancy_value_paise=disc_val,
                    is_nrv_lower_than_cost=is_nrv_low,
                    audit_remark=remark,
                )
            )

        return InventoryObservationSummary(
            total_items_counted=len(count_sheets),
            matched_items_count=matched_cnt,
            shortage_items_count=shortage_cnt,
            excess_items_count=excess_cnt,
            obsolete_items_count=obsolete_cnt,
            total_shortage_value_paise=tot_shortage_val,
            records=records,
        )
