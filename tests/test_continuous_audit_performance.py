"""Performance scalability benchmarks for Phase F continuous audit evaluation engines."""

from datetime import date
import time
import pytest

from finauditpro.domain.journal_analytics_engine import JournalAnalyticsEngine
from finauditpro.domain.pattern_detection_engine import PatternDetectionEngine


def test_performance_10k_transactions() -> None:
    """Benchmark evaluating 10,000 journal entries for deterministic risk factors."""
    journal_engine = JournalAnalyticsEngine(period_end_date=date(2025, 3, 31))

    # Generate 10,000 synthetic transaction records
    records = []
    for i in range(10_000):
        records.append({
            "id": f"ROW-{i}",
            "voucher_number": f"VCH-{i}",
            "voucher_type": "JOURNAL" if i % 10 == 0 else "SALES",
            "entry_date": "2025-03-29" if i % 50 == 0 else "2024-10-15",
            "account_code": f"{1000 + (i % 50)}",
            "account_name": "Cash In Hand" if i % 100 == 0 else "Customer Account",
            "debit_paise": 10000000 if i % 25 == 0 else (12345 + i),
            "credit_paise": 0,
            "narration": f"Transaction description record {i}",
            "created_by_raw": "admin" if i % 200 == 0 else "clerk_1",
        })

    t0 = time.perf_counter()
    alerts = []
    for r in records:
        alert = journal_engine.evaluate_journal_entry("ENG-PERF", r)
        if alert:
            alerts.append(alert)
    elapsed = time.perf_counter() - t0

    # 10k transactions evaluated in under 1.5 seconds
    assert elapsed < 1.5, f"10k transactions evaluation took {elapsed:.2f}s (expected < 1.5s)"
    assert len(alerts) > 0


def test_performance_100k_benford_analysis() -> None:
    """Benchmark calculating Benford's Law distribution across 100,000 transactions."""
    journal_engine = JournalAnalyticsEngine()

    # Generate 100,000 amounts
    amounts = [int(1000 * (1.0001 ** i)) + (i % 9999) for i in range(100_000)]

    t0 = time.perf_counter()
    res = journal_engine.analyze_benford_distribution(amounts)
    elapsed = time.perf_counter() - t0

    # 100k transactions analyzed in under 0.5 seconds
    assert elapsed < 0.5, f"100k Benford analysis took {elapsed:.2f}s (expected < 0.5s)"
    assert res.population_count == 100_000
    assert res.eligible_count > 90_000
