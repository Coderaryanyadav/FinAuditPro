"""Unit tests for substantive audit engines: Three-Way Match, Cut-Off, BRS, and DSC Signing."""

from finauditpro.domain.bank_reconciliation_engine import (
    BankReconciliationEngine,
    BRSExceptionSeverityEnum,
    BRSItemTypeEnum,
)
from finauditpro.domain.cutoff_testing_engine import (
    CutOffExceptionTypeEnum,
    CutOffPeriodEnum,
    CutOffTestingEngine,
)
from finauditpro.domain.dsc_signing_engine import (
    CertificateTypeEnum,
    DSCCertificateMetadata,
    DSCSigningEngine,
)
from finauditpro.domain.three_way_match_engine import (
    MatchDiscrepancyTypeEnum,
    ThreeWayMatchEngine,
)


def test_three_way_match_engine() -> None:
    """Verify Three-Way PO-GRN-Invoice rate and quantity variance detection."""
    orders = [
        # Matched
        {
            "po_number": "PO-01", "grn_number": "GRN-01", "invoice_number": "INV-01",
            "po_quantity": 100, "grn_quantity": 100, "invoice_quantity": 100,
            "po_rate_paise": 50000, "invoice_rate_paise": 50000, "invoice_total_paise": 5000000,
        },
        # Quantity Discrepancy (Billed 100, received 80)
        {
            "po_number": "PO-02", "grn_number": "GRN-02", "invoice_number": "INV-02",
            "po_quantity": 100, "grn_quantity": 80, "invoice_quantity": 100,
            "po_rate_paise": 50000, "invoice_rate_paise": 50000, "invoice_total_paise": 5000000,
        },
        # Invoice Without GRN
        {
            "po_number": "PO-03", "grn_number": "", "invoice_number": "INV-03",
            "po_quantity": 50, "grn_quantity": 0, "invoice_quantity": 50,
            "po_rate_paise": 20000, "invoice_rate_paise": 20000, "invoice_total_paise": 1000000,
        },
    ]

    res = ThreeWayMatchEngine.match_orders("eng-01", orders)
    assert res.total_matched_orders == 3
    assert res.fully_matched_count == 1
    assert res.discrepancy_count == 2
    assert res.records[0].discrepancy_type == MatchDiscrepancyTypeEnum.MATCHED
    assert res.records[1].discrepancy_type == MatchDiscrepancyTypeEnum.QUANTITY_VARIANCE
    assert res.records[2].discrepancy_type == MatchDiscrepancyTypeEnum.INVOICE_WITHOUT_GRN


def test_cutoff_testing_engine() -> None:
    """Verify sales cut-off and post-year-end sales return exception flagging."""
    txns = [
        # Normal sales pre-year end
        {
            "document_number": "S-101", "document_date": "2026-03-28", "dispatch_or_receipt_date": "2026-03-28",
            "amount_paise": 10000000, "transaction_type": "Sales",
        },
        # Post year-end sales return within 15 days
        {
            "document_number": "SR-01", "document_date": "2026-04-05", "dispatch_or_receipt_date": "2026-04-05",
            "amount_paise": 50000000, "transaction_type": "Returns",
        },
    ]

    res = CutOffTestingEngine.analyze_cutoff_records("eng-01", "2026-03-31", txns)
    assert res.total_inspected_items == 2
    assert res.clean_items_count == 1
    assert res.exception_count == 1
    assert res.records[1].exception_type == CutOffExceptionTypeEnum.POST_YEAR_END_SALES_RETURN
    assert res.records[1].period_classification == CutOffPeriodEnum.POST_YEAR_END


def test_bank_reconciliation_engine() -> None:
    """Verify BRS stale cheque (>90 days) and delayed banking exception identification."""
    items = [
        # Normal timing difference (20 days)
        {
            "bank_account_number": "HDFC-01", "item_type": BRSItemTypeEnum.UNPRESENTED_CHEQUE,
            "entry_date": "2026-03-15", "amount_paise": 2500000,
        },
        # Stale Cheque (120 days old)
        {
            "bank_account_number": "HDFC-01", "item_type": BRSItemTypeEnum.UNPRESENTED_CHEQUE,
            "entry_date": "2025-12-01", "amount_paise": 8000000,
        },
        # Delayed deposit (30 days)
        {
            "bank_account_number": "HDFC-01", "item_type": BRSItemTypeEnum.UNCREDITED_DEPOSIT,
            "entry_date": "2026-03-01", "amount_paise": 15000000,
        },
    ]

    res = BankReconciliationEngine.audit_brs_statement("eng-01", "2026-03-31", items)
    assert res.total_reconciling_items == 3
    assert res.stale_cheques_count == 1
    assert res.delayed_deposits_count == 1
    assert res.records[1].exception_severity == BRSExceptionSeverityEnum.STALE_CHEQUE_REVERSAL


def test_dsc_signing_engine() -> None:
    """Verify X.509 DSC cryptographic signature generation and payload hashing."""
    cert = DSCCertificateMetadata(
        subject_common_name="CA Aryan Yadav, FCA",
        issuer_name="e-Mudhra CA",
        membership_number="543210",
        certificate_serial="EMU-88990011",
        valid_from="2025-01-01",
        valid_to="2027-12-31",
        sha256_fingerprint="a1b2c3d4e5f6...",
        certificate_type=CertificateTypeEnum.CLASS_3_INDIVIDUAL,
    )

    payload = b"Independent Auditor's Report FY 2024-25 Final Approved Copy"
    res = DSCSigningEngine.sign_audit_artifact(
        engagement_id="eng-01",
        document_target="Report: Statutory Audit Report FY 2024-25",
        artifact_bytes=payload,
        cert_metadata=cert,
    )

    assert res.is_success is True
    assert res.signature_record is not None
    assert res.signature_record.signatory_icai_membership == "543210"
    assert res.signature_record.is_valid is True
    assert "digitally signed" in res.status_message
