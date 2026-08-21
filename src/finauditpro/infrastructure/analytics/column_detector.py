"""Intelligent column inspection and canonical field auto-detection engine for audit datasets."""

import re

STANDARD_AUDIT_FIELDS: dict[str, list[str]] = {
    "date": ["date", "txn_date", "posting_date", "vch_date", "invoice_date", "trans_date", "dt", "value_date"],
    "counterparty_gstin": ["counterparty_gstin", "vendor_gstin", "customer_gstin", "gstin", "party_gstin"],
    "voucher_type": ["voucher_type", "vch_type", "type", "doc_type", "transaction_type"],
    "voucher_number": ["voucher_no", "vch_no", "voucher_number", "invoice_number", "invoice_no", "inv_no", "document_no", "ref_no", "txn_id", "transaction_id"],
    "invoice_number": ["voucher_no", "vch_no", "voucher_number", "invoice_number", "invoice_no", "inv_no", "document_no", "ref_no", "txn_id", "transaction_id"],
    "account_code": ["account_code", "acc_code", "ledger_code", "code", "acc_no", "vendor_code", "customer_code"],
    "account_name": ["account_name", "account", "ledger", "particulars", "account_head", "party", "party_name", "vendor_name", "customer_name", "vendor", "description"],
    "account_type": ["account_type", "type", "category", "group"],
    "opening_dr": ["opening_dr", "op_dr", "opening_debit", "op_debit", "opening_dr_amount"],
    "opening_cr": ["opening_cr", "op_cr", "opening_credit", "op_credit", "opening_cr_amount"],
    "debit": ["debit", "dr", "dr_amount", "withdrawal", "debit_amount", "debit_paise"],
    "credit": ["credit", "cr", "cr_amount", "deposit", "credit_amount", "credit_paise"],
    "closing_dr": ["closing_dr", "cl_dr", "closing_debit", "cl_debit"],
    "closing_cr": ["closing_cr", "cl_cr", "closing_credit", "cl_credit"],
    "balance": ["balance", "running_balance", "closing_balance", "bal"],
    "narration": ["narration", "description", "remarks", "memo", "note", "narrative"],
    "reference": ["reference", "ref", "cheque_no", "chq_no", "ref_number"],
    "created_by": ["created_by", "user", "entered_by", "prepared_by"],
}


def _clean_header_name(header: str) -> str:
    """Normalize header string for keyword matching."""
    return re.sub(r"[^a-z0-9]", "_", str(header).strip().lower()).strip("_")


def detect_column_mappings(
    headers: list[str], sample_rows: list[dict[str, str]] | None = None
) -> dict[str, str]:
    """Auto-detect standard canonical audit field mapping candidates from raw file headers."""
    mappings: dict[str, str] = {}
    normalized_headers = {h: _clean_header_name(h) for h in headers}
    assigned_cols: set[str] = set()

    # Pass 1: Exact Keyword Match
    for std_field, keywords in STANDARD_AUDIT_FIELDS.items():
        for raw_h, norm_h in normalized_headers.items():
            if raw_h not in assigned_cols and norm_h in keywords:
                mappings[std_field] = raw_h
                assigned_cols.add(raw_h)
                break

    # Pass 2: Substring Keyword Match for remaining unassigned fields
    for std_field, keywords in STANDARD_AUDIT_FIELDS.items():
        if std_field in mappings:
            continue
        for raw_h, norm_h in normalized_headers.items():
            if raw_h not in assigned_cols and any(kw in norm_h for kw in keywords):
                mappings[std_field] = raw_h
                assigned_cols.add(raw_h)
                break

    if "voucher_number" in mappings and "invoice_number" not in mappings:
        mappings["invoice_number"] = mappings["voucher_number"]

    return mappings
