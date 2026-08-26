"""Pure domain entities and testing logic for Fixed Asset Register Verification and CARO 3(i) reporting."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class AssetAnomalyTypeEnum(StrEnum):
    CLEAN_ASSET = "Verified Active Fixed Asset"
    NEGATIVE_NET_BOOK_VALUE = "Negative Net Book Value (Over-Depreciation Error)"
    GHOST_ASSET_UNLOCATED = "Ghost Asset (Capitalized but Unlocated in Physical Verification)"
    CWIP_AGEING_STAGNANT = "Stagnant Capital Work-in-Progress (>2 Years Ageing)"
    INCOMPLETE_TITLE_DEEDS = "Title Deeds Not Held in Name of Company (CARO 3(i)(c))"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class FixedAssetAuditRecord(DomainBaseModel):
    """Fixed asset record evaluated for physical existence and CARO 2020 3(i) compliance."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    asset_tag: str = Field(...)
    asset_name: str = Field(...)
    gross_block_paise: int = Field(default=0, ge=0)
    accumulated_depreciation_paise: int = Field(default=0, ge=0)
    net_book_value_paise: int = Field(default=0)
    location: str = Field(default="Factory Floor")
    is_physically_verified: bool = Field(default=True)
    title_deeds_in_company_name: bool = Field(default=True)
    cwip_age_months: int = Field(default=0, ge=0)
    anomaly_type: AssetAnomalyTypeEnum = Field(default=AssetAnomalyTypeEnum.CLEAN_ASSET)
    caro_disclosure_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class FixedAssetAuditSummary:
    total_assets_inspected: int
    clean_assets_count: int
    anomalous_assets_count: int
    total_gross_block_paise: int
    at_risk_carrying_value_paise: int
    records: list[FixedAssetAuditRecord]


class FixedAssetEngine:
    """Deterministic audit engine for Fixed Asset Register reconciliation and CARO 2020 3(i) verification."""

    @classmethod
    def audit_fixed_asset_register(
        cls,
        engagement_id: str,
        asset_records: list[dict[str, Any]],
    ) -> FixedAssetAuditSummary:
        """Evaluate Fixed Asset Register for ghost assets, negative NBV, stagnant CWIP, and title deeds."""
        records = []
        clean_cnt = 0
        anomaly_cnt = 0
        tot_gross_paise = 0
        at_risk_paise = 0

        for a in asset_records:
            tag = a.get("asset_tag", "")
            name = a.get("asset_name", "General Fixed Asset")
            gross = int(a.get("gross_block_paise", a.get("gross_block", 0) * 100))
            dep = int(a.get("accumulated_depreciation_paise", a.get("accumulated_depreciation", 0) * 100))
            nbv = gross - dep
            loc = a.get("location", "Factory Floor")
            phys_ver = a.get("is_physically_verified", True)
            title_ok = a.get("title_deeds_in_company_name", True)
            cwip_age = int(a.get("cwip_age_months", 0))
            tot_gross_paise += gross

            anomaly = AssetAnomalyTypeEnum.CLEAN_ASSET
            remark = "Fixed asset verified against register and physical count."

            if nbv < 0:
                anomaly = AssetAnomalyTypeEnum.NEGATIVE_NET_BOOK_VALUE
                remark = f"Negative Net Book Value: Gross ₹{gross/100:,.2f} vs Accumulated Dep ₹{dep/100:,.2f}. Depreciation calculation error."
                anomaly_cnt += 1
                at_risk_paise += abs(nbv)
            elif not phys_ver:
                anomaly = AssetAnomalyTypeEnum.GHOST_ASSET_UNLOCATED
                remark = f"Asset '{name}' (Carrying Value ₹{nbv/100:,.2f}) not located during physical verification. Possible ghost asset."
                anomaly_cnt += 1
                at_risk_paise += max(0, nbv)
            elif not title_ok:
                anomaly = AssetAnomalyTypeEnum.INCOMPLETE_TITLE_DEEDS
                remark = "Immovable property title deeds not held in company's name. Specific disclosure required under CARO 2020 Clause 3(i)(c)."
                anomaly_cnt += 1
                at_risk_paise += gross
            elif cwip_age > 24:
                anomaly = AssetAnomalyTypeEnum.CWIP_AGEING_STAGNANT
                remark = f"CWIP project has been stagnant for {cwip_age} months (>2 years). Evaluate impairment under AS 28 / Ind AS 36."
                anomaly_cnt += 1
                at_risk_paise += gross
            else:
                clean_cnt += 1

            records.append(
                FixedAssetAuditRecord(
                    engagement_id=engagement_id,
                    asset_tag=tag,
                    asset_name=name,
                    gross_block_paise=gross,
                    accumulated_depreciation_paise=dep,
                    net_book_value_paise=nbv,
                    location=loc,
                    is_physically_verified=phys_ver,
                    title_deeds_in_company_name=title_ok,
                    cwip_age_months=cwip_age,
                    anomaly_type=anomaly,
                    caro_disclosure_remark=remark,
                )
            )

        return FixedAssetAuditSummary(
            total_assets_inspected=len(asset_records),
            clean_assets_count=clean_cnt,
            anomalous_assets_count=anomaly_cnt,
            total_gross_block_paise=tot_gross_paise,
            at_risk_carrying_value_paise=at_risk_paise,
            records=records,
        )
