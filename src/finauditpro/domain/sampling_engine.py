"""Pure domain entities and algorithms for SA 530 Audit Sampling and Monetary Unit Sampling (MUS)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class SamplingMethodEnum(StrEnum):
    MONETARY_UNIT_SAMPLING = "Monetary Unit Sampling (MUS)"
    SYSTEMATIC_SAMPLING = "Systematic Sampling"
    RANDOM_SAMPLING = "Random Selection"
    HIGH_VALUE_STRATIFICATION = "High-Value Stratification"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class SamplingPlan(DomainBaseModel):
    """Configured and reproducible SA 530 sampling plan."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    dataset_id: str = Field(...)
    name: str = Field(..., min_length=1)
    sampling_method: SamplingMethodEnum = Field(default=SamplingMethodEnum.MONETARY_UNIT_SAMPLING)
    population_count: int = Field(..., ge=1)
    population_value_paise: int = Field(..., ge=0)
    tolerable_misstatement_paise: int = Field(..., ge=0)
    expected_misstatement_paise: int = Field(default=0, ge=0)
    confidence_level_pct: float = Field(default=95.0)
    sampling_interval_paise: int = Field(default=0)
    calculated_sample_size: int = Field(default=0)
    selected_sample_indices: list[int] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class SamplingResult:
    sample_size: int
    sampling_interval_paise: int
    selected_items: list[dict[str, Any]]
    high_value_items: list[dict[str, Any]]
    total_sampled_value_paise: int
    rationale: str


class AuditSamplingEngine:
    """Deterministic mathematical engine for SA 530 statistical and monetary unit sampling."""

    RELIABILITY_FACTORS: ClassVar[dict[float, float]] = {
        90.0: 2.31,
        95.0: 3.00,
        99.0: 4.61,
    }


    @classmethod
    def calculate_mus_sample(
        cls,
        population_records: list[dict[str, Any]],
        tolerable_misstatement_paise: int,
        expected_misstatement_paise: int = 0,
        confidence_level_pct: float = 95.0,
    ) -> SamplingResult:
        """Execute Monetary Unit Sampling (MUS) with cumulative monetary interval selection."""
        if not population_records:
            return SamplingResult(0, 0, [], [], 0, "Empty population.")

        pop_val_paise = sum(int(r.get("amount_paise", r.get("amount", 0) * 100)) for r in population_records)
        factor = cls.RELIABILITY_FACTORS.get(confidence_level_pct, 3.0)

        # Tolerable minus expected misstatement expansion
        net_tolerable = max(1, tolerable_misstatement_paise - expected_misstatement_paise)
        interval = max(1, int(net_tolerable / factor))

        # 1. Stratify High-Value Items (Items >= Sampling Interval)
        high_value = []
        regular_pop = []
        for idx, rec in enumerate(population_records):
            amt = int(rec.get("amount_paise", rec.get("amount", 0) * 100))
            item_data = dict(rec)
            item_data["original_index"] = idx + 1
            item_data["amount_paise"] = amt
            if amt >= interval:
                high_value.append(item_data)
            else:
                regular_pop.append(item_data)

        # 2. Cumulative Monetary Unit Selection on Remaining Population
        selected_sample = list(high_value)
        cum_sum = 0
        target = interval

        for item in regular_pop:
            amt = item["amount_paise"]
            cum_sum += amt
            if cum_sum >= target:
                selected_sample.append(item)
                target += interval

        total_sampled_val = sum(i["amount_paise"] for i in selected_sample)
        rationale = (
            f"SA 530 MUS Plan: Population {len(population_records)} items (₹{pop_val_paise / 100:,.2f}). "
            f"Tolerable Misstatement: ₹{tolerable_misstatement_paise / 100:,.2f} at {confidence_level_pct}% Confidence. "
            f"Sampling Interval: ₹{interval / 100:,.2f}. Selected {len(high_value)} high-value and {len(selected_sample) - len(high_value)} interval items."
        )

        return SamplingResult(
            sample_size=len(selected_sample),
            sampling_interval_paise=interval,
            selected_items=selected_sample,
            high_value_items=high_value,
            total_sampled_value_paise=total_sampled_val,
            rationale=rationale,
        )
