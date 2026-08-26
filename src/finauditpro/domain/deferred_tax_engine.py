"""Pure domain entities and testing logic for Deferred Tax Asset/Liability (DTA/DTL) timing differences."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class TimingDifferenceTypeEnum(StrEnum):
    DEPRECIATION_DIFFERENCE = "Depreciation (Companies Act vs IT Act Sec 32)"
    SECTION_43B_DISALLOWANCE = "Statutory Dues / Bonus / Leave Disallowance (Sec 43B)"
    SECTION_40A7_GRATUITY = "Unapproved Gratuity / Provision (Sec 40A(7))"
    UNABSORBED_LOSS_DEPRECIATION = "Unabsorbed Business Loss & Depreciation Carryforward"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class DeferredTaxItem(DomainBaseModel):
    """Timing difference item evaluated for DTA/DTL computation under AS 22 / Ind AS 12."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    item_name: str = Field(...)
    difference_type: TimingDifferenceTypeEnum = Field(...)
    books_carrying_paise: int = Field(default=0)
    tax_base_paise: int = Field(default=0)
    timing_difference_paise: int = Field(default=0)  # Positive = Taxable, Negative = Deductible
    tax_rate_pct: float = Field(default=25.17)  # Standard corporate tax rate incl surcharge/cess
    is_dta: bool = Field(default=False)  # True = Deferred Tax Asset, False = Deferred Tax Liability
    tax_impact_paise: int = Field(default=0)
    audit_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class DeferredTaxSummary:
    total_taxable_differences_paise: int
    total_deductible_differences_paise: int
    net_deferred_tax_liability_paise: int
    net_deferred_tax_asset_paise: int
    effective_tax_rate_pct: float
    items: list[DeferredTaxItem]


class DeferredTaxEngine:
    """Deterministic calculation engine for AS 22 / Ind AS 12 Income Taxes."""

    @classmethod
    def calculate_deferred_tax(
        cls,
        engagement_id: str,
        tax_rate_pct: float,
        timing_items: list[dict[str, Any]],
    ) -> DeferredTaxSummary:
        """Calculate DTA/DTL schedule across book depreciation, Section 43B items, and losses."""
        records = []
        tot_taxable = 0
        tot_deductible = 0

        rate_factor = tax_rate_pct / 100.0

        for itm in timing_items:
            name = itm.get("item_name", "General Timing Item")
            diff_t = itm.get("difference_type", TimingDifferenceTypeEnum.DEPRECIATION_DIFFERENCE)
            b_val = int(itm.get("books_carrying_paise", 0))
            t_val = int(itm.get("tax_base_paise", 0))

            # Timing diff = Books - Tax Base
            diff = b_val - t_val
            tax_impact = int(abs(diff) * rate_factor)

            # In asset terms: If Book Value > Tax Base -> Future taxable -> DTL
            # In expense terms: If 43B disallowed in books -> Future deductible -> DTA
            is_asset = diff < 0 or diff_t in (
                TimingDifferenceTypeEnum.SECTION_43B_DISALLOWANCE,
                TimingDifferenceTypeEnum.SECTION_40A7_GRATUITY,
                TimingDifferenceTypeEnum.UNABSORBED_LOSS_DEPRECIATION,
            )

            if is_asset:
                tot_deductible += abs(diff)
                rem = f"DTA of ₹{tax_impact/100:,.2f} recognized. Verify virtual/reasonable certainty for realization."
            else:
                tot_taxable += abs(diff)
                rem = f"DTL of ₹{tax_impact/100:,.2f} created due to higher tax depreciation in initial years."

            records.append(
                DeferredTaxItem(
                    engagement_id=engagement_id,
                    item_name=name,
                    difference_type=diff_t,
                    books_carrying_paise=b_val,
                    tax_base_paise=t_val,
                    timing_difference_paise=diff,
                    tax_rate_pct=tax_rate_pct,
                    is_dta=is_asset,
                    tax_impact_paise=tax_impact,
                    audit_remark=rem,
                )
            )

        net_dtl = max(0, int((tot_taxable - tot_deductible) * rate_factor))
        net_dta = max(0, int((tot_deductible - tot_taxable) * rate_factor))

        return DeferredTaxSummary(
            total_taxable_differences_paise=tot_taxable,
            total_deductible_differences_paise=tot_deductible,
            net_deferred_tax_liability_paise=net_dtl,
            net_deferred_tax_asset_paise=net_dta,
            effective_tax_rate_pct=tax_rate_pct,
            items=records,
        )
