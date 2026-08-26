"""Pure domain entities and materiality allocation algorithms for SA 600 Group Audits."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class ComponentTypeEnum(StrEnum):
    HOLDING_PARENT = "Holding / Parent Entity"
    SUBSIDIARY_SIGNIFICANT = "Significant Subsidiary (Financial Benchmark > 15%)"
    SUBSIDIARY_NON_SIGNIFICANT = "Non-Significant Component"
    ASSOCIATE_OR_JV = "Associate / Joint Venture (Equity Method)"
    BRANCH_OFFICE = "Operating Domestic / Foreign Branch"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class GroupComponent(DomainBaseModel):
    """Component entity in consolidated group financial statement audit under SA 600."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    component_name: str = Field(..., min_length=1)
    component_type: ComponentTypeEnum = Field(...)
    country_of_incorporation: str = Field(default="India")
    component_auditor_name: str = Field(default="Independent CA / CPA Firm")
    is_audited_by_principal_auditor: bool = Field(default=False)
    revenue_paise: int = Field(default=0, ge=0)
    assets_paise: int = Field(default=0, ge=0)
    component_materiality_paise: int = Field(default=0, ge=0)
    group_revenue_share_pct: float = Field(default=0.0)
    group_assets_share_pct: float = Field(default=0.0)
    sa600_clearance_received: bool = Field(default=False)
    audit_instructions_sent: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class GroupAuditSummary:
    total_components_count: int
    significant_components_count: int
    total_group_revenue_paise: int
    total_group_assets_paise: int
    components: list[GroupComponent]
    group_conclusion: str


class GroupAuditEngine:
    """Deterministic allocation engine for SA 600 Group Component Materiality and Significance."""

    @classmethod
    def analyze_group_structure(
        cls,
        engagement_id: str,
        overall_group_materiality_paise: int,
        components_data: list[dict[str, Any]],
    ) -> GroupAuditSummary:
        """Calculate component significance (>15% benchmark) and assign component materiality."""
        tot_rev = sum(int(c.get("revenue_paise", c.get("revenue", 0) * 100)) for c in components_data)
        tot_assets = sum(int(c.get("assets_paise", c.get("assets", 0) * 100)) for c in components_data)

        records = []
        sig_cnt = 0

        for c in components_data:
            name = c.get("component_name", "Component")
            c_auditor = c.get("component_auditor_name", "Independent Firm")
            by_principal = c.get("is_audited_by_principal_auditor", False)
            country = c.get("country_of_incorporation", "India")
            rev = int(c.get("revenue_paise", c.get("revenue", 0) * 100))
            assets = int(c.get("assets_paise", c.get("assets", 0) * 100))

            rev_pct = round((rev / tot_rev * 100.0), 2) if tot_rev > 0 else 0.0
            asset_pct = round((assets / tot_assets * 100.0), 2) if tot_assets > 0 else 0.0

            # Significant if > 15% of Group Revenue or Total Assets
            is_significant = rev_pct >= 15.0 or asset_pct >= 15.0
            c_type = ComponentTypeEnum.SUBSIDIARY_SIGNIFICANT if is_significant else ComponentTypeEnum.SUBSIDIARY_NON_SIGNIFICANT
            if is_significant:
                sig_cnt += 1

            # Component materiality set to between 50% and 80% of Group Materiality (pro-rated by size)
            size_weight = max(0.5, min(0.8, (rev_pct + asset_pct) / 200.0 * 2))
            c_materiality = int(overall_group_materiality_paise * size_weight)

            records.append(
                GroupComponent(
                    engagement_id=engagement_id,
                    component_name=name,
                    component_type=c_type,
                    country_of_incorporation=country,
                    component_auditor_name=c_auditor,
                    is_audited_by_principal_auditor=by_principal,
                    revenue_paise=rev,
                    assets_paise=assets,
                    component_materiality_paise=c_materiality,
                    group_revenue_share_pct=rev_pct,
                    group_assets_share_pct=asset_pct,
                    sa600_clearance_received=c.get("sa600_clearance_received", False),
                    audit_instructions_sent=c.get("audit_instructions_sent", True),
                )
            )

        conclusion = (
            f"SA 600 Group Structure: {len(components_data)} components identified. "
            f"{sig_cnt} significant components requiring formal group audit instructions and component clearance."
        )

        return GroupAuditSummary(
            total_components_count=len(components_data),
            significant_components_count=sig_cnt,
            total_group_revenue_paise=tot_rev,
            total_group_assets_paise=tot_assets,
            components=records,
            group_conclusion=conclusion,
        )
