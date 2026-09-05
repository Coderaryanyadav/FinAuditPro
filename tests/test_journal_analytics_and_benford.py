"""Unit tests for Journal Analytics Engine risk factor decomposition and Benford's Law."""

from datetime import date

import pytest

from finauditpro.domain.continuous_audit_entities import AlertSeverityEnum
from finauditpro.domain.journal_analytics_engine import JournalAnalyticsEngine


def test_journal_entry_risk_scoring_and_decomposition() -> None:
    engine = JournalAnalyticsEngine(
        period_end_date=date(2025, 3, 31),
        high_value_threshold_paise=50_00_00_00,  # ₹50 Lakhs
    )

    # 1. Low risk journal (regular workday, non-round normal amount)
    low_risk_entry = {
        "voucher_number": "JV-101",
        "voucher_type": "PURCHASE",
        "entry_date": "2024-11-12",  # Tuesday
        "account_code": "5001",
        "account_name": "Office Supplies",
        "debit_paise": 143285,  # ₹1,432.85
        "credit_paise": 0,
        "narration": "Monthly stationery purchase invoice 8821",
        "created_by_raw": "staff_acc_1",
    }
    alert = engine.evaluate_journal_entry("ENG-1", low_risk_entry)
    assert alert is None  # Score below 30 threshold

    # 2. High risk journal: Round number ₹9,99,999 on weekend 2 days before period end, manual JV
    high_risk_entry = {
        "voucher_number": "JV-999",
        "voucher_type": "MANUAL_JOURNAL",
        "entry_date": "2025-03-30",  # Sunday, 1 day before FY close
        "account_code": "1001",
        "account_name": "Cash In Hand",
        "debit_paise": 99999900,  # ₹9,99,999.00
        "credit_paise": 0,
        "narration": "Direct cash revenue adjustment for month end",
        "created_by_raw": "admin",
    }
    alert = engine.evaluate_journal_entry("ENG-1", high_risk_entry)
    assert alert is not None
    assert alert.severity in (AlertSeverityEnum.CRITICAL, AlertSeverityEnum.HIGH)
    assert alert.risk_score >= 70.0

    # Ensure risk score is completely transparent and decomposed into individual factors
    factor_names = {f.factor_name for f in alert.risk_factors}
    assert "Threshold-Proximity Pattern" in factor_names
    assert "High-Value Transaction" in factor_names
    assert "Weekend Posting" in factor_names
    assert "Period-End Close Posting" in factor_names
    assert "Manual Journal Entry" in factor_names
    assert "Unusual Account Combination" in factor_names
    assert "Privileged/Generic User Poster" in factor_names

    # Sum of factor scores should equal total score
    calc_sum = sum(f.score_contribution for f in alert.risk_factors)
    assert alert.risk_score == pytest.approx(calc_sum, 0.01)


def test_benfords_law_analytical_indicator() -> None:
    engine = JournalAnalyticsEngine()

    # Natural Benford-conforming distribution (powers of 1.15)
    benford_population = [int(1000 * (1.15 ** i)) for i in range(1, 100)]
    result = engine.analyze_benford_distribution(benford_population)

    assert result.digit_type == "FIRST_DIGIT"
    assert result.label == "Analytical anomaly indicator"
    assert "conclusive evidence" in result.limitations.lower()
    assert result.eligible_count > 50
    assert result.p_value_approx >= 0.0

    # Highly anomalous uniform/artificial distribution (all amounts starting with '9')
    artificial_population = [900000 + i * 100 for i in range(200)]
    anomaly_result = engine.analyze_benford_distribution(artificial_population)

    assert anomaly_result.deviation_detected is True
    assert anomaly_result.chi_square_stat > 15.507
    assert "statistically significant divergence" in anomaly_result.interpretation
