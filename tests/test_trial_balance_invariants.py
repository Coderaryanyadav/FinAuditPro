"""Automated unit tests for Trial Balance zero-balance invariants and paise normalization."""

from finauditpro.domain.financial_entities import TrialBalanceSummary
from finauditpro.infrastructure.financial.currency_parser import (
    parse_indian_currency,
    sanitize_export_cell,
)
from finauditpro.infrastructure.financial.financial_importer import FinancialImporter


def test_parse_indian_currency_various_formats() -> None:
    """Test standard Indian and international accounting currency formats."""
    # Standard Indian separators
    assert parse_indian_currency("1,23,456.78").paise == 12345678
    assert parse_indian_currency("₹ 50,000.50").paise == 5000050
    assert parse_indian_currency("$1,000").paise == 100000

    # Negative accounting parentheses
    assert parse_indian_currency("(25,000.00)").paise == -2500000
    assert parse_indian_currency("-1,500.25").paise == -150025

    # Empty / null equivalents
    assert parse_indian_currency("").paise == 0
    assert parse_indian_currency(None).paise == 0
    assert parse_indian_currency("NaN").paise == 0
    assert parse_indian_currency("-").paise == 0
    assert parse_indian_currency("null").paise == 0


def test_sanitize_export_cell_formula_injection() -> None:
    """Test protection against CSV formula injection."""
    assert sanitize_export_cell("=1+1") == "'=1+1"
    assert sanitize_export_cell("+2+2") == "'+2+2"
    assert sanitize_export_cell("-3+3") == "'-3+3"
    assert sanitize_export_cell("@cmd") == "'@cmd"
    assert sanitize_export_cell("\t123") == "'\t123"
    assert sanitize_export_cell("Normal Text") == "Normal Text"


def test_trial_balance_summary_balanced() -> None:
    """Test TrialBalanceSummary invariant checks for balanced ledger."""
    summary = TrialBalanceSummary(
        total_opening_dr_paise=1000000,
        total_opening_cr_paise=1000000,
        total_debit_paise=5000000,
        total_credit_paise=5000000,
        total_closing_dr_paise=6000000,
        total_closing_cr_paise=6000000,
    )
    assert summary.is_opening_balanced is True
    assert summary.is_period_balanced is True
    assert summary.is_closing_balanced is True
    assert summary.is_balanced is True
    assert summary.period_discrepancy_paise == 0
    assert summary.closing_discrepancy_paise == 0
    assert summary.opening_discrepancy_paise == 0


def test_trial_balance_summary_out_of_balance() -> None:
    """Test TrialBalanceSummary invariant checks for out-of-balance ledger with exact discrepancies."""
    summary = TrialBalanceSummary(
        total_opening_dr_paise=1000000,
        total_opening_cr_paise=950000,  # 50,000 paise diff
        total_debit_paise=5000000,
        total_credit_paise=4850000,  # 150,000 paise diff
        total_closing_dr_paise=6000000,
        total_closing_cr_paise=5800000,  # 200,000 paise diff
    )
    assert summary.is_opening_balanced is False
    assert summary.is_period_balanced is False
    assert summary.is_closing_balanced is False
    assert summary.is_balanced is False
    assert summary.opening_discrepancy_paise == 50000
    assert summary.period_discrepancy_paise == 150000
    assert summary.closing_discrepancy_paise == 200000


def test_import_trial_balance_balanced() -> None:
    """Test import_trial_balance with balanced row data."""
    rows = [
        {"Code": "1001", "Name": "Cash in Hand", "Dr": "1,00,000.00", "Cr": "0.00"},
        {"Code": "2001", "Name": "Share Capital", "Dr": "0.00", "Cr": "1,00,000.00"},
    ]
    mappings = {
        "account_code": "Code",
        "account_name": "Name",
        "debit": "Dr",
        "credit": "Cr",
    }
    result = FinancialImporter.import_trial_balance("ds-1", rows, mappings)
    assert len(result.valid_rows) == 2
    assert len(result.errors) == 0
    assert result.summary is not None
    assert result.summary.is_balanced is True
    assert result.summary.total_debit_paise == 10000000
    assert result.summary.total_credit_paise == 10000000


def test_import_trial_balance_out_of_balance_flags_discrepancy() -> None:
    """Test that out-of-balance TB import flags the exact discrepancy in paise and formatted INR."""
    rows = [
        {
            "Code": "1001",
            "Name": "Cash in Hand",
            "Dr": "1,50,000.00",
            "Cr": "0.00",
            "ClDr": "1,50,000.00",
            "ClCr": "0.00",
        },
        {
            "Code": "2001",
            "Name": "Share Capital",
            "Dr": "0.00",
            "Cr": "1,00,000.00",
            "ClDr": "0.00",
            "ClCr": "1,00,000.00",
        },
    ]
    mappings = {
        "account_code": "Code",
        "account_name": "Name",
        "debit": "Dr",
        "credit": "Cr",
        "closing_dr": "ClDr",
        "closing_cr": "ClCr",
    }
    result = FinancialImporter.import_trial_balance("ds-2", rows, mappings)
    assert len(result.valid_rows) == 2
    assert len(result.errors) >= 1

    # Verify period movement discrepancy error
    period_err = next((e for e in result.errors if e.column_name == "debit/credit"), None)
    assert period_err is not None
    assert "50,000" in period_err.error_reason or "5000000" in period_err.error_reason

    # Verify summary invariants
    assert result.summary is not None
    assert result.summary.is_period_balanced is False
    assert result.summary.period_discrepancy_paise == 5000000  # ₹50,000.00 = 5,000,000 paise
