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


def test_monetary_unit_sampling_engine() -> None:
    """Verify SA 530 Monetary Unit Sampling (MUS) interval calculation and high-value item stratification."""
    from finauditpro.domain.sampling_engine import AuditSamplingEngine

    pop = [
        {"voucher": "V-01", "amount_paise": 20000000},   # ₹2L
        {"voucher": "V-02", "amount_paise": 150000000},  # ₹15L (High Value >= Interval)
        {"voucher": "V-03", "amount_paise": 30000000},   # ₹3L
        {"voucher": "V-04", "amount_paise": 50000000},   # ₹5L
        {"voucher": "V-05", "amount_paise": 10000000},   # ₹1L
    ]
    # Tolerable misstatement: ₹30L -> Interval = 30L / 3.0 = ₹10L (10,00,000 paise * 100 = 100,000,000 paise)
    res = AuditSamplingEngine.calculate_mus_sample(
        population_records=pop,
        tolerable_misstatement_paise=300000000,
        expected_misstatement_paise=0,
        confidence_level_pct=95.0,
    )

    assert res.sample_size >= 1
    assert len(res.high_value_items) == 1
    assert res.high_value_items[0]["voucher"] == "V-02"
    assert "SA 530 MUS Plan" in res.rationale


def test_going_concern_evaluation_engine() -> None:
    """Verify SA 570 Going Concern financial indicator evaluation and reporting disclosures."""
    from finauditpro.domain.going_concern_engine import GoingConcernEngine, SolvencyRiskLevelEnum

    # Critical Solvency Flag (Negative Net Worth + Operating Losses)
    level, report_req, text = GoingConcernEngine.evaluate_indicators(
        has_operating_losses=True,
        has_negative_operating_cashflow=True,
        has_negative_net_worth=True,
        has_covenant_breaches=False,
        has_debt_maturity_unfunded=True,
    )
    assert level == SolvencyRiskLevelEnum.CRITICAL_GOING_CONCERN_RISK
    assert report_req is True
    assert "Material Uncertainty Related to Going Concern" in text


def test_gst_reconciliation_engine() -> None:
    """Verify GSTR-2B vs Purchase Register 3-way matching and ITC eligibility logic."""
    from finauditpro.domain.gst_reconciliation_engine import (
        GSTReconciliationEngine,
        MatchStatusEnum,
    )

    books = [
        {"invoice_number": "INV-001", "vendor_gstin": "27AAACB1234F1Z5", "tax_paise": 1800000, "is_sec_17_5_blocked": False},  # Matched
        {"invoice_number": "INV-002", "vendor_gstin": "27AAACB1234F1Z5", "tax_paise": 500000, "is_sec_17_5_blocked": True},   # Ineligible Sec 17(5)
        {"invoice_number": "INV-003", "vendor_gstin": "27XYZAB9999F1Z1", "tax_paise": 2400000, "is_sec_17_5_blocked": False},  # Missing in 2B
    ]
    gstr2b = [
        {"invoice_number": "INV-001", "vendor_gstin": "27AAACB1234F1Z5", "tax_paise": 1800000},
    ]

    res = GSTReconciliationEngine.match_purchase_register_with_2b("eng-01", books, gstr2b)
    assert res.total_vouchers == 3
    assert res.matched_count == 1
    assert res.ineligible_count == 1
    assert res.mismatched_count == 1
    assert res.records[0].match_status == MatchStatusEnum.MATCHED
    assert res.records[1].match_status == MatchStatusEnum.ITC_INELIGIBLE_SEC_17_5
    assert res.records[2].match_status == MatchStatusEnum.MISSING_IN_2B


def test_related_party_scan_engine() -> None:
    """Verify SA 550 detection of undisclosed transactions with common KMP PAN matches."""
    from finauditpro.domain.related_party_engine import (
        RelatedPartyCategoryEnum,
        RelatedPartyEngine,
        RelatedPartyEntity,
    )

    declared = [
        RelatedPartyEntity(
            engagement_id="eng-01",
            party_name="Apex Holdings Pvt Ltd",
            relationship_category=RelatedPartyCategoryEnum.HOLDING_SUBSIDIARY,
        )
    ]
    txns = [
        {"account_name": "Apex Holdings Pvt Ltd", "amount_paise": 50000000, "pan": "AAACA1111A", "has_audit_committee_approval": True},
        {"account_name": "Secret Vendor Logistics", "amount_paise": 25000000, "pan": "ABCDE1234F", "has_audit_committee_approval": False},
    ]
    directors_pans = ["ABCDE1234F"]  # Matching the undeclared vendor

    res = RelatedPartyEngine.scan_ledger_against_kmp_master(declared, txns, directors_pans)
    assert res.total_transactions == 2
    assert res.unapproved_count == 1
    assert len(res.undeclared_vendor_matches) == 1
    assert res.undeclared_vendor_matches[0]["account_name"] == "SECRET VENDOR LOGISTICS"




