"""Unit tests for deterministic financial analytics algorithms."""

from finauditpro.infrastructure.analytics.analytics_engine import DeterministicAnalyticsEngine


def test_duplicate_transaction_detection() -> None:
    records = [
        {
            "row_index": 1,
            "date": "2026-04-10",
            "amount": 150000.0,
            "account_name": "Consulting Fees",
            "transaction_id": "TXN101",
        },
        {
            "row_index": 2,
            "date": "2026-04-10",
            "amount": 150000.0,
            "account_name": "Consulting Fees",
            "transaction_id": "TXN102",
        },
        {
            "row_index": 3,
            "date": "2026-04-11",
            "amount": 200000.0,
            "account_name": "Rent",
            "transaction_id": "TXN103",
        },
    ]

    out = DeterministicAnalyticsEngine.find_duplicates(records)
    assert out.anomaly_count == 2
    assert len(out.anomalies) == 2
    assert "Duplicate transaction indicator" in out.anomalies[0].rationale


def test_high_value_transaction_anomaly() -> None:
    records = [
        {
            "row_index": 1,
            "date": "2026-04-10",
            "amount": 250000.0,
            "account_name": "Office Supplies",
        },
        {
            "row_index": 2,
            "date": "2026-04-12",
            "amount": 750000.0,
            "account_name": "Plant & Machinery",
        },
    ]

    out = DeterministicAnalyticsEngine.find_large_amounts(records, threshold=500000.0)
    assert out.anomaly_count == 1
    assert out.anomalies[0].row_index == 2
    assert out.anomalies[0].amount == 750000.0


def test_round_number_anomaly() -> None:
    records = [
        {"row_index": 1, "date": "2026-04-10", "amount": 123456.0, "account_name": "Vendor A"},
        {"row_index": 2, "date": "2026-04-12", "amount": 1000000.0, "account_name": "Vendor B"},
    ]

    out = DeterministicAnalyticsEngine.find_round_numbers(records, min_amount=100000.0)
    assert out.anomaly_count == 1
    assert out.anomalies[0].row_index == 2
    assert out.anomalies[0].amount == 1000000.0


def test_weekend_posting_anomaly() -> None:
    records = [
        {
            "row_index": 1,
            "date": "2026-04-10",
            "amount": 50000.0,
            "account_name": "Friday Payment",
        },  # Friday
        {
            "row_index": 2,
            "date": "2026-04-11",
            "amount": 50000.0,
            "account_name": "Saturday Payment",
        },  # Saturday
        {
            "row_index": 3,
            "date": "2026-04-12",
            "amount": 50000.0,
            "account_name": "Sunday Payment",
        },  # Sunday
    ]

    out = DeterministicAnalyticsEngine.find_weekend_transactions(records)
    assert out.anomaly_count == 2
    row_indices = [a.row_index for a in out.anomalies]
    assert 2 in row_indices and 3 in row_indices


def test_sequence_gap_detection() -> None:
    records = [
        {
            "row_index": 1,
            "transaction_id": "INV-1001",
            "invoice_number": "INV-1001",
            "amount": 100.0,
        },
        {
            "row_index": 2,
            "transaction_id": "INV-1002",
            "invoice_number": "INV-1002",
            "amount": 200.0,
        },
        {
            "row_index": 3,
            "transaction_id": "INV-1005",
            "invoice_number": "INV-1005",
            "amount": 500.0,
        },
    ]

    out = DeterministicAnalyticsEngine.find_sequence_gaps(records)
    assert out.anomaly_count == 1
    assert "Gap of 2 missing" in out.anomalies[0].rationale
