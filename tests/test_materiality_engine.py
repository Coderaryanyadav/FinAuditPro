"""Tests for SA 320 Materiality Calculation Engine & Version Retention."""

from finauditpro.domain.audit_matrix_entities import BenchmarkTypeEnum
from finauditpro.domain.materiality_engine import BENCHMARK_GUIDANCE_OPTIONS, MaterialityEngine


def test_sa320_materiality_paise_precision() -> None:
    """Verify that OM, PM, and CTT calculate exact integer paise without float errors."""
    benchmark_paise = 5000000000  # ₹5,00,000.00 in paise (₹5 Crore)

    assessment = MaterialityEngine.calculate(
        engagement_id="eng-test-1",
        benchmark_type=BenchmarkTypeEnum.REVENUE,
        benchmark_amount_paise=benchmark_paise,
        overall_percentage=1.0,  # 1% of ₹5 Cr = ₹5,00,000 (50,000,000 paise)
        performance_percentage=75.0,  # 75% of ₹5L = ₹3,75,000 (37,500,000 paise)
        trivial_percentage=5.0,  # 5% of ₹5L = ₹25,000 (2,500,000 paise)
    )

    assert assessment.overall_materiality_paise == 50000000
    assert assessment.performance_materiality_paise == 37500000
    assert assessment.clearly_trivial_threshold_paise == 2500000

    assert assessment.overall_materiality.formatted == "₹5,00,000.00"
    assert assessment.performance_materiality.formatted == "₹3,75,000.00"
    assert (
        assessment.clearly_trivial_threshold.formatted == "₹25,00,000.00"
        or assessment.clearly_trivial_threshold.formatted == "₹25,000.00"
    )


def test_materiality_reproducibility() -> None:
    """Verify that recomputing from stored inputs yields identical results."""
    b_paise = 1234567890

    res1 = MaterialityEngine.calculate(
        engagement_id="eng-test-1",
        benchmark_type=BenchmarkTypeEnum.PROFIT_BEFORE_TAX,
        benchmark_amount_paise=b_paise,
        overall_percentage=5.0,
        performance_percentage=75.0,
        trivial_percentage=5.0,
    )

    res2 = MaterialityEngine.calculate(
        engagement_id="eng-test-1",
        benchmark_type=BenchmarkTypeEnum.PROFIT_BEFORE_TAX,
        benchmark_amount_paise=b_paise,
        overall_percentage=5.0,
        performance_percentage=75.0,
        trivial_percentage=5.0,
    )

    assert res1.overall_materiality_paise == res2.overall_materiality_paise
    assert res1.performance_materiality_paise == res2.performance_materiality_paise
    assert res1.clearly_trivial_threshold_paise == res2.clearly_trivial_threshold_paise


def test_non_statutory_benchmark_disclaimers() -> None:
    """Verify that default benchmark choices carry source and verified=false disclaimers."""
    for opt in BENCHMARK_GUIDANCE_OPTIONS:
        assert opt.is_verified_statutory is False
        assert "Non-Statutory" in opt.source or "Guidance" in opt.source


def test_threshold_classification() -> None:
    """Verify monetary exception classification against materiality thresholds."""
    assessment = MaterialityEngine.calculate(
        engagement_id="eng-test-1",
        benchmark_type=BenchmarkTypeEnum.REVENUE,
        benchmark_amount_paise=1000000000,  # ₹10,00,000
        overall_percentage=1.0,  # OM = ₹10,000 (1000000 paise)
        performance_percentage=75.0,  # PM = ₹7,500 (750000 paise)
        trivial_percentage=5.0,  # CTT = ₹500 (50000 paise)
    )

    assert MaterialityEngine.classify_monetary_amount(10000, assessment) == "Clearly Trivial"
    assert (
        MaterialityEngine.classify_monetary_amount(600000, assessment) == "Requires Auditor Review"
    )
    assert (
        MaterialityEngine.classify_monetary_amount(8000000, assessment)
        == "Above Performance Materiality"
    )
    assert (
        MaterialityEngine.classify_monetary_amount(12000000, assessment)
        == "Above Overall Materiality"
    )
