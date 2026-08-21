"""Unit tests for column header inspection and auto-detection."""

from finauditpro.infrastructure.analytics.column_detector import detect_column_mappings


def test_column_detector_standard_csv_headers() -> None:
    headers = ["Posting Date", "Account Name", "Vch No", "Debit", "Credit", "Particulars", "GSTIN"]
    mappings = detect_column_mappings(headers)

    assert mappings.get("date") == "Posting Date"
    assert mappings.get("account_name") == "Account Name"
    assert mappings.get("invoice_number") == "Vch No"
    assert mappings.get("debit") == "Debit"
    assert mappings.get("credit") == "Credit"
    assert mappings.get("counterparty_gstin") == "GSTIN"


def test_column_detector_alternative_names() -> None:
    headers = ["Trans_Date", "Ledger", "Withdrawal", "Deposit", "Remarks", "Vendor_GSTIN"]
    mappings = detect_column_mappings(headers)

    assert mappings.get("date") == "Trans_Date"
    assert mappings.get("account_name") == "Ledger"
    assert mappings.get("debit") == "Withdrawal"
    assert mappings.get("credit") == "Deposit"
    assert mappings.get("narration") == "Remarks"
    assert mappings.get("counterparty_gstin") == "Vendor_GSTIN"
