import random
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
    JUDGMENTAL = "Judgmental Selection"
    HUNDRED_PERCENT = "100% Testing"


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
    random_seed: int | None = Field(default=None)
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

        pop_val_paise = sum(
            int(r.get("amount_paise", r.get("amount", 0) * 100)) for r in population_records
        )
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

    @classmethod
    def calculate_random_sample(
        cls,
        population_records: list[dict[str, Any]],
        sample_size: int,
        random_seed: int | None = None,
    ) -> SamplingResult:
        """Reproducible random sampling under SA 530 using pseudo-random seed."""
        if not population_records or sample_size <= 0:
            return SamplingResult(0, 0, [], [], 0, "Empty population or non-positive sample size.")

        n = min(sample_size, len(population_records))
        rng = random.Random(random_seed) if random_seed is not None else random.Random(42)
        indexed = []
        for idx, r in enumerate(population_records):
            item = dict(r)
            item["original_index"] = idx + 1
            item["amount_paise"] = int(r.get("amount_paise", r.get("amount", 0) * 100))
            indexed.append(item)

        selected = rng.sample(indexed, n)
        tot_val = sum(i["amount_paise"] for i in selected)
        rationale = (
            f"SA 530 Random Selection: Sampled {n} items from population of {len(population_records)} "
            f"(Seed: {random_seed if random_seed is not None else 'Default(42)'})."
        )
        return SamplingResult(
            sample_size=n,
            sampling_interval_paise=0,
            selected_items=selected,
            high_value_items=[],
            total_sampled_value_paise=tot_val,
            rationale=rationale,
        )

    @classmethod
    def calculate_systematic_sample(
        cls,
        population_records: list[dict[str, Any]],
        sample_size: int,
        start_index: int = 0,
    ) -> SamplingResult:
        """Systematic sampling selecting items at fixed intervals (k = N / n)."""
        if not population_records or sample_size <= 0:
            return SamplingResult(0, 0, [], [], 0, "Empty population or non-positive sample size.")

        N = len(population_records)
        n = min(sample_size, N)
        k = max(1, N // n)

        indexed = []
        for idx, r in enumerate(population_records):
            item = dict(r)
            item["original_index"] = idx + 1
            item["amount_paise"] = int(r.get("amount_paise", r.get("amount", 0) * 100))
            indexed.append(item)

        selected = []
        curr = start_index % k
        while curr < N and len(selected) < n:
            selected.append(indexed[curr])
            curr += k

        tot_val = sum(i["amount_paise"] for i in selected)
        rationale = (
            f"SA 530 Systematic Selection: Selected {len(selected)} items with interval k={k} "
            f"from population of {N}."
        )
        return SamplingResult(
            sample_size=len(selected),
            sampling_interval_paise=k,
            selected_items=selected,
            high_value_items=[],
            total_sampled_value_paise=tot_val,
            rationale=rationale,
        )

    @classmethod
    def calculate_judgmental_sample(
        cls,
        population_records: list[dict[str, Any]],
        threshold_paise: int | None = None,
        filter_key: str | None = None,
    ) -> SamplingResult:
        """Judgmental / targeted sampling based on auditor assessment and risk thresholds."""
        if not population_records:
            return SamplingResult(0, 0, [], [], 0, "Empty population.")

        selected = []
        for idx, r in enumerate(population_records):
            item = dict(r)
            item["original_index"] = idx + 1
            amt = int(r.get("amount_paise", r.get("amount", 0) * 100))
            item["amount_paise"] = amt
            if threshold_paise is not None and amt >= threshold_paise:
                selected.append(item)
            elif filter_key and r.get(filter_key):
                selected.append(item)

        if not selected and threshold_paise is None and not filter_key:
            selected = [
                dict(
                    r,
                    original_index=idx + 1,
                    amount_paise=int(r.get("amount_paise", r.get("amount", 0) * 100)),
                )
                for idx, r in enumerate(population_records[:10])
            ]

        tot_val = sum(i["amount_paise"] for i in selected)
        rationale = (
            f"SA 530 Judgmental Selection: Selected {len(selected)} targeted items "
            f"(Threshold: ₹{(threshold_paise or 0) / 100:,.2f})."
        )
        return SamplingResult(
            sample_size=len(selected),
            sampling_interval_paise=0,
            selected_items=selected,
            high_value_items=selected,
            total_sampled_value_paise=tot_val,
            rationale=rationale,
        )

    @classmethod
    def calculate_100_pct_sample(
        cls,
        population_records: list[dict[str, Any]],
    ) -> SamplingResult:
        """100% examination of all items in the population under SA 530."""
        if not population_records:
            return SamplingResult(0, 0, [], [], 0, "Empty population.")

        selected = []
        for idx, r in enumerate(population_records):
            item = dict(r)
            item["original_index"] = idx + 1
            item["amount_paise"] = int(r.get("amount_paise", r.get("amount", 0) * 100))
            selected.append(item)

        tot_val = sum(i["amount_paise"] for i in selected)
        rationale = f"SA 530 100% Testing: Complete examination of all {len(selected)} items."
        return SamplingResult(
            sample_size=len(selected),
            sampling_interval_paise=1,
            selected_items=selected,
            high_value_items=selected,
            total_sampled_value_paise=tot_val,
            rationale=rationale,
        )
