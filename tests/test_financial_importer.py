"""Unit tests for financial importer, Decimal currency parsing, date parsing, formula injection protection, and Excel/CSV ingestion."""

from pathlib import Path

import pytest

from finauditpro.infrastructure.financial.financial_importer import (
    FinancialImporter,
    parse_indian_currency,
    parse_indian_date,
    sanitize_export_cell,
)


def test_parse_indian_currency() -> None:
    # Standard Indian formatting
    m1 = parse_indian_currency("1,23,456.78")
    assert m1.paise == 12345678
    assert m1.formatted == "₹1,23,456.78"

    # Decimal string with no separators
    m2 = parse_indian_currency("500000.50")
    assert m2.paise == 50000050

    # Clean zero / empty
    assert parse_indian_currency("").paise == 0
    assert parse_indian_currency("-").paise == 0
    assert parse_indian_currency(None).paise == 0

    # Unparseable invalid string raises ValueError
    with pytest.raises(ValueError):
        parse_indian_currency("INVALID_CURRENCY_CELL")


def test_parse_indian_date() -> None:
    assert parse_indian_date("31-03-2026") == "2026-03-31"
    assert parse_indian_date("01/04/2025") == "2025-04-01"
    assert parse_indian_date("2026-03-31") == "2026-03-31"
    assert parse_indian_date("") is None

    with pytest.raises(ValueError):
        parse_indian_date("NOT_A_DATE")


def test_sanitize_export_cell() -> None:
    # Formula triggers get prefixed with a single quote
    assert sanitize_export_cell("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_export_cell("+100") == "'+100"
    assert sanitize_export_cell("-500") == "'-500"
    assert sanitize_export_cell("@cmd") == "'@cmd"
    assert sanitize_export_cell("Normal Text") == "Normal Text"


def test_import_real_trial_balance_fixture() -> None:
    fixture_path = Path(
        "tests/fixtures/AuditPro_Input_Client_Trial_Balance_Sample_V1.0_04Jan2026.xlsx"
    )
    if not fixture_path.is_file():
        pytest.skip("Fixture file not found.")

    headers, rows = FinancialImporter.read_tabular_rows(fixture_path)
    assert len(headers) > 0
    assert len(rows) > 0

    mappings = {
        "account_code": "Account Code",
        "account_name": "Account Name",
        "opening_dr": "Opening Dr",
        "opening_cr": "Opening Cr",
        "debit": "Debit",
        "credit": "Credit",
        "closing_dr": "Closing Dr",
        "closing_cr": "Closing Cr",
    }

    res = FinancialImporter.import_trial_balance("ds-tb-101", rows, mappings)
    assert res.total_rows == len(rows)
    assert len(res.valid_rows) > 0
    assert len(res.errors) == 0


def test_import_real_general_ledger_fixture() -> None:
    fixture_path = Path(
        "tests/fixtures/AuditPro_Input_General_Ledger_Extract_Sample_V1.0_04Jan2026.xlsx"
    )
    if not fixture_path.is_file():
        pytest.skip("Fixture file not found.")

    headers, rows = FinancialImporter.read_tabular_rows(fixture_path)
    assert len(rows) > 0

    mappings = {
        "date": "Date",
        "voucher_type": "Voucher Type",
        "voucher_number": "Voucher No",
        "account_code": "Account Code",
        "account_name": "Account",
        "debit": "Debit",
        "credit": "Credit",
        "narration": "Narration",
    }

    res = FinancialImporter.import_general_ledger("ds-gl-101", rows, mappings)
    assert len(res.valid_rows) > 0
