"""Unit tests for deterministic analytics routines and repeatability verification."""

from finauditpro.domain.financial_entities import BankTransaction, LedgerEntry, TrialBalanceLine
from finauditpro.infrastructure.analytics.analytics_engine import DeterministicAnalyticsEngine


def test_trial_balance_balances_analytic() -> None:
    lines = [
        TrialBalanceLine(
            dataset_id="ds1",
            source_row_no=2,
            account_name="Share Capital",
            debit_paise=0,
            credit_paise=10000000,
        ),
        TrialBalanceLine(
            dataset_id="ds1",
            source_row_no=3,
            account_name="Cash at Bank",
            debit_paise=10000000,
            credit_paise=0,
        ),
    ]

    res = DeterministicAnalyticsEngine.check_trial_balance_balances("ds1", lines)
    assert len(res.exceptions) == 0  # Balanced!

    # Create imbalance
    imbalanced_lines = [
        TrialBalanceLine(
            dataset_id="ds1",
            source_row_no=2,
            account_name="Share Capital",
            debit_paise=0,
            credit_paise=10000000,
        ),
        TrialBalanceLine(
            dataset_id="ds1",
            source_row_no=3,
            account_name="Cash at Bank",
            debit_paise=9000000,
            credit_paise=0,
        ),
    ]
    res_imb = DeterministicAnalyticsEngine.check_trial_balance_balances("ds1", imbalanced_lines)
    assert len(res_imb.exceptions) == 1
    assert "₹10,000.00" in res_imb.exceptions[0].description


def test_bank_balance_continuity_analytic() -> None:
    txns = [
        BankTransaction(
            dataset_id="b1",
            source_row_no=2,
            txn_date="2026-04-01",
            description="Opening Balance",
            debit_paise=0,
            credit_paise=0,
            balance_paise=10000000,
        ),
        BankTransaction(
            dataset_id="b1",
            source_row_no=3,
            txn_date="2026-04-02",
            description="Vendor Payment",
            debit_paise=2000000,
            credit_paise=0,
            balance_paise=8000000,
        ),
        BankTransaction(
            dataset_id="b1",
            source_row_no=4,
            txn_date="2026-04-03",
            description="Customer Receipt",
            debit_paise=0,
            credit_paise=5000000,
            balance_paise=12000000,
        ),  # Break! Expected 13000000
    ]

    res = DeterministicAnalyticsEngine.check_bank_balance_continuity("b1", txns)
    assert len(res.exceptions) == 1
    assert res.exceptions[0].implicated_rows == [4]


def test_duplicate_detection_analytic() -> None:
    entries = [
        LedgerEntry(
            dataset_id="gl1",
            source_row_no=2,
            entry_date="2026-04-05",
            account_name="Consulting Fees",
            debit_paise=5000000,
            credit_paise=0,
        ),
        LedgerEntry(
            dataset_id="gl1",
            source_row_no=3,
            entry_date="2026-04-05",
            account_name="Consulting Fees",
            debit_paise=5000000,
            credit_paise=0,
        ),  # Duplicate
    ]

    res = DeterministicAnalyticsEngine.detect_duplicates("gl1", entries)
    assert len(res.exceptions) == 1
    assert res.exceptions[0].implicated_rows == [2, 3]


def test_weekend_postings_analytic() -> None:
    entries = [
        LedgerEntry(
            dataset_id="gl1",
            source_row_no=2,
            entry_date="2026-04-04",
            account_name="Cash",
            debit_paise=100000,
        ),  # Saturday
        LedgerEntry(
            dataset_id="gl1",
            source_row_no=3,
            entry_date="2026-04-06",
            account_name="Cash",
            debit_paise=100000,
        ),  # Monday
    ]

    res = DeterministicAnalyticsEngine.detect_weekend_postings("gl1", entries)
    assert len(res.exceptions) == 1
    assert res.exceptions[0].implicated_rows == [2]


def test_analytics_repeatability_determinism() -> None:
    """PROVE that running analytics twice on identical input yields 100% identical outputs."""
    entries = [
        LedgerEntry(
            dataset_id="gl1",
            source_row_no=2,
            entry_date="2026-04-05",
            voucher_number="VCH-100",
            account_name="Rent",
            debit_paise=10000000,
        ),
        LedgerEntry(
            dataset_id="gl1",
            source_row_no=3,
            entry_date="2026-04-05",
            voucher_number="VCH-100",
            account_name="Rent",
            debit_paise=10000000,
        ),
    ]

    res1 = DeterministicAnalyticsEngine.detect_duplicates("gl1", entries)
    res2 = DeterministicAnalyticsEngine.detect_duplicates("gl1", entries)

    assert len(res1.exceptions) == len(res2.exceptions)
    assert res1.exceptions[0].computed_evidence == res2.exceptions[0].computed_evidence


def test_schedule_iii_ratios_computation() -> None:
    """Verify Schedule III statutory financial ratio calculations and threshold exception flagging."""
    # Current Assets < Current Liabilities (CR < 1.0) & Debt > 2.5x Equity
    res = DeterministicAnalyticsEngine.compute_schedule_iii_ratios(
        dataset_id="ds-stat-01",
        current_assets_paise=80000000,       # ₹8,00,000.00
        current_liabilities_paise=100000000, # ₹10,00,000.00 -> CR = 0.8
        net_profit_paise=15000000,           # ₹1,50,000.00
        revenue_paise=100000000,             # ₹10,00,000.00 -> NPM = 15.0%
        total_debt_paise=300000000,          # ₹30,00,000.00
        shareholder_equity_paise=100000000,  # ₹10,00,000.00 -> DER = 3.0
    )

    assert res.parameters["current_ratio"] == 0.8
    assert res.parameters["net_profit_margin_pct"] == 15.0
    assert res.parameters["debt_equity_ratio"] == 3.0
    assert len(res.exceptions) == 2
    assert any("Current Ratio" in e.title for e in res.exceptions)
    assert any("Debt-Equity" in e.title for e in res.exceptions)


def test_trade_payables_msme_ageing() -> None:
    """Verify Schedule III trade payables MSMED Act Section 15 45-day overdue exception detection."""
    records = [
        {"vendor_name": "ABC Tech MSME", "is_msme": True, "days_overdue": 62, "amount_paise": 45000000},  # ₹4.5L Overdue >45d
        {"vendor_name": "Standard Corp Non-MSME", "is_msme": False, "days_overdue": 90, "amount_paise": 100000000},
        {"vendor_name": "XYZ Spares MSME", "is_msme": True, "days_overdue": 20, "amount_paise": 15000000},  # Within 45d
    ]

    res = DeterministicAnalyticsEngine.analyze_trade_payables_ageing("ds-ap-01", records)
    assert res.parameters["total_vendors"] == 3
    assert res.parameters["msme_overdue_paise"] == 45000000
    assert len(res.exceptions) == 1
    assert "MSME Payment Overdue > 45 Days: ABC Tech MSME" in res.exceptions[0].title
    assert "Section 15 of MSMED Act" in res.exceptions[0].description


