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


def test_payroll_forensic_engine() -> None:
    """Verify ghost employee detection via duplicate bank accounts and inactive staff checks."""
    from finauditpro.domain.payroll_forensic_engine import (
        PayrollAnomalyTypeEnum,
        PayrollForensicEngine,
    )

    entries = [
        # Normal staff
        {"employee_code": "EMP-01", "employee_name": "Ramesh Kumar", "bank_account_number": "SBIN001122", "salary_paise": 5000000, "is_active": True},
        # Duplicate bank account (Ghost employee)
        {"employee_code": "EMP-02", "employee_name": "Ghost Staff 1", "bank_account_number": "SBIN001122", "salary_paise": 5000000, "is_active": True},
        # Inactive employee paid post-resignation
        {"employee_code": "EMP-03", "employee_name": "Suresh Ex-Employee", "bank_account_number": "HDFC998877", "salary_paise": 4000000, "is_active": False, "resignation_date": "2025-11-30"},
    ]

    res = PayrollForensicEngine.scan_payroll_master("eng-01", entries)
    assert res.total_payroll_entries == 3
    assert res.ghost_employee_anomalies_count == 3
    assert res.records[0].anomaly_type == PayrollAnomalyTypeEnum.DUPLICATE_BANK_ACCOUNT
    assert res.records[1].anomaly_type == PayrollAnomalyTypeEnum.DUPLICATE_BANK_ACCOUNT
    assert res.records[2].anomaly_type == PayrollAnomalyTypeEnum.PAYMENT_TO_INACTIVE_EMPLOYEE



def test_inventory_count_engine() -> None:
    """Verify SA 501 physical inventory test count reconciliation against perpetual records."""
    from finauditpro.domain.inventory_count_engine import (
        InventoryCountEngine,
        InventoryDiscrepancyTypeEnum,
    )

    sheets = [
        # Matched count
        {"item_code": "ITM-01", "book_quantity": 100, "physical_count_quantity": 100, "unit_cost_paise": 5000},
        # Physical Shortage (pilferage / unrecorded issue)
        {"item_code": "ITM-02", "book_quantity": 50, "physical_count_quantity": 40, "unit_cost_paise": 10000},
        # Damaged stock (NRV test required)
        {"item_code": "ITM-03", "book_quantity": 20, "physical_count_quantity": 20, "unit_cost_paise": 8000, "is_damaged_or_obsolete": True},
    ]

    res = InventoryCountEngine.reconcile_physical_counts("eng-01", sheets)
    assert res.total_items_counted == 3
    assert res.matched_items_count == 1
    assert res.shortage_items_count == 1
    assert res.obsolete_items_count == 1
    assert res.records[1].discrepancy_type == InventoryDiscrepancyTypeEnum.PHYSICAL_SHORTAGE
    assert res.records[2].discrepancy_type == InventoryDiscrepancyTypeEnum.DAMAGED_OR_OBSOLETE


def test_fixed_asset_engine() -> None:
    """Verify CARO 2020 3(i) Fixed Asset verification for ghost assets and negative NBV."""
    from finauditpro.domain.fixed_asset_engine import AssetAnomalyTypeEnum, FixedAssetEngine

    assets = [
        # Valid asset
        {"asset_tag": "FA-01", "asset_name": "CNC Lathe Machine", "gross_block_paise": 100000000, "accumulated_depreciation_paise": 20000000, "is_physically_verified": True},
        # Negative NBV (Depreciation calculation error)
        {"asset_tag": "FA-02", "asset_name": "Old Generator", "gross_block_paise": 50000000, "accumulated_depreciation_paise": 60000000, "is_physically_verified": True},
        # Ghost Asset (Not located during physical verification)
        {"asset_tag": "FA-03", "asset_name": "Executive Laptop #4", "gross_block_paise": 8000000, "accumulated_depreciation_paise": 2000000, "is_physically_verified": False},
    ]

    res = FixedAssetEngine.audit_fixed_asset_register("eng-01", assets)
    assert res.total_assets_inspected == 3
    assert res.clean_assets_count == 1
    assert res.anomalous_assets_count == 2
    assert res.records[1].anomaly_type == AssetAnomalyTypeEnum.NEGATIVE_NET_BOOK_VALUE
    assert res.records[2].anomaly_type == AssetAnomalyTypeEnum.GHOST_ASSET_UNLOCATED



def test_independence_conflict_engine() -> None:
    """Verify team independence verification, holding limit breaches, and Section 144 prohibitions."""
    from finauditpro.domain.independence_engine import (
        IndependenceConflictEngine,
        IndependenceThreatTypeEnum,
    )

    declarations = [
        # Clean Member
        {"user_id": "u-01", "user_name": "Audit Senior", "role": "Senior", "holding_face_value_paise": 5000000},  # ₹50,000 <= ₹2L
        # Holding Limit Exceeded (> ₹2L)
        {"user_id": "u-02", "user_name": "Audit Partner B", "role": "Partner", "holding_face_value_paise": 35000000},  # ₹3.5L > ₹2L
        # Section 144 Prohibited Service
        {"user_id": "u-03", "user_name": "Manager C", "role": "Manager", "has_prohibited_non_audit_services": True},
    ]

    res = IndependenceConflictEngine.evaluate_team_independence("firm-01", "eng-01", declarations)
    assert res.total_declarations == 3
    assert res.clean_count == 1
    assert res.impaired_count == 2
    assert res.declarations[1].threat_type == IndependenceThreatTypeEnum.FINANCIAL_INTEREST_EXCEEDS_LIMIT
    assert res.declarations[2].threat_type == IndependenceThreatTypeEnum.SECTION_144_PROHIBITED_SERVICE
    assert "IMPAIRED" in res.firm_compliance_status


def test_deferred_tax_engine() -> None:
    """Verify AS 22 / Ind AS 12 Deferred Tax calculation on depreciation and Section 43B disallowances."""
    from finauditpro.domain.deferred_tax_engine import DeferredTaxEngine, TimingDifferenceTypeEnum

    items = [
        # Higher book depreciation than tax -> Future deductible -> DTA
        {"item_name": "Plant & Machinery Depreciation", "difference_type": TimingDifferenceTypeEnum.DEPRECIATION_DIFFERENCE, "books_carrying_paise": 80000000, "tax_base_paise": 100000000},
        # Section 43B statutory dues unpaid -> DTA
        {"item_name": "Bonus Payable under Sec 43B", "difference_type": TimingDifferenceTypeEnum.SECTION_43B_DISALLOWANCE, "books_carrying_paise": 15000000, "tax_base_paise": 0},
    ]

    res = DeferredTaxEngine.calculate_deferred_tax("eng-01", 25.17, items)
    assert len(res.items) == 2
    assert res.net_deferred_tax_asset_paise > 0
    assert res.items[1].is_dta is True


def test_receivables_recovery_engine() -> None:
    """Verify trade receivables subsequent cash recovery tie-out and ECL provisioning."""
    from finauditpro.domain.receivables_recovery_engine import (
        ReceivablesRecoveryEngine,
        RecoveryStatusEnum,
    )

    balances = [
        {"debtor_code": "D-01", "debtor_name": "Alpha Corp", "balance_at_year_end_paise": 10000000},
        {"debtor_code": "D-02", "debtor_name": "Beta Enterprises", "balance_at_year_end_paise": 20000000},
        {"debtor_code": "D-03", "debtor_name": "Gamma Solutions", "balance_at_year_end_paise": 15000000},
    ]
    receipts = [
        {"debtor_code": "D-01", "receipt_amount_paise": 10000000},  # 100% recovered
        {"debtor_code": "D-02", "receipt_amount_paise": 8000000},   # Partially recovered
    ]

    res = ReceivablesRecoveryEngine.tie_out_subsequent_receipts("eng-01", balances, receipts)
    assert res.total_debtors_count == 3
    assert res.fully_recovered_count == 1
    assert res.partially_recovered_count == 1
    assert res.unrecovered_count == 1
    assert res.records[0].recovery_status == RecoveryStatusEnum.FULLY_RECOVERED
    assert res.records[1].recovery_status == RecoveryStatusEnum.PARTIALLY_RECOVERED
    assert res.records[2].recovery_status == RecoveryStatusEnum.UNRECOVERED_OVERDUE


def test_minutes_contradiction_engine() -> None:
    """Verify Section 180(1)(c) borrowing resolution limit breach detection against general ledger."""
    from finauditpro.domain.minutes_contradiction_engine import (
        ContradictionSeverityEnum,
        MinutesContradictionEngine,
        MinutesItemTypeEnum,
    )

    resolutions = [
        {
            "meeting_date": "2025-09-15", "resolution_type": MinutesItemTypeEnum.BORROWING_LIMIT_RESOLUTION,
            "authorized_limit_paise": 5000000000, "extracted_text": "Resolved that borrowing limit is ₹50 Cr.",
        }
    ]
    # Actual ledger borrowings: ₹60 Cr (> ₹50 Cr limit)
    balances = {"total_borrowings_paise": 6000000000}

    res = MinutesContradictionEngine.analyze_resolutions("eng-01", resolutions, balances)
    assert res.total_resolutions_scanned == 1
    assert res.contradictions_count == 1
    assert res.records[0].severity == ContradictionSeverityEnum.BORROWING_LIMIT_BREACH


def test_roc_secretarial_engine() -> None:
    """Verify MCA Form MGT-7 paid-up capital and CHG-1 charge registration reconciliation."""
    from finauditpro.domain.roc_secretarial_engine import (
        ROCDiscrepancyTypeEnum,
        ROCFormTypeEnum,
        ROCSecretarialEngine,
    )

    filings = [
        # MGT-7 Match
        {"form_type": ROCFormTypeEnum.FORM_MGT_7, "srn_number": "SRN-12345", "reported_value_paise": 100000000},
        # CHG-1 Deficit (Registered ₹3 Cr vs Borrowings ₹5 Cr)
        {"form_type": ROCFormTypeEnum.FORM_CHG_1, "srn_number": "SRN-99887", "reported_value_paise": 300000000},
    ]
    books = {
        "paid_up_capital_paise": 100000000,
        "secured_loans_paise": 500000000,
    }

    res = ROCSecretarialEngine.reconcile_mca_filings("eng-01", filings, books)
    assert res.total_filings_checked == 2
    assert res.compliant_count == 1
    assert res.discrepancy_count == 1
    assert res.records[1].discrepancy_type == ROCDiscrepancyTypeEnum.UNREGISTERED_CHARGE_ON_ASSETS


def test_group_audit_engine() -> None:
    """Verify SA 600 Group Audit component significance benchmark (>15%) and component materiality allocation."""
    from finauditpro.domain.group_audit_engine import (
        ComponentTypeEnum,
        GroupAuditEngine,
    )

    comps = [
        # Significant subsidiary (50% of revenue)
        {"component_name": "Apex Manufacturing Ltd", "revenue_paise": 5000000000, "assets_paise": 4000000000},
        # Non-significant subsidiary (5% of revenue)
        {"component_name": "Apex Small Spares LLP", "revenue_paise": 500000000, "assets_paise": 400000000},
    ]

    res = GroupAuditEngine.analyze_group_structure(
        engagement_id="eng-group-01",
        overall_group_materiality_paise=100000000,  # ₹1 Cr Group Materiality
        components_data=comps,
    )

    assert res.total_components_count == 2
    assert res.significant_components_count == 1
    assert res.components[0].component_type == ComponentTypeEnum.SUBSIDIARY_SIGNIFICANT
    assert res.components[1].component_type == ComponentTypeEnum.SUBSIDIARY_NON_SIGNIFICANT
    assert res.components[0].component_materiality_paise > res.components[1].component_materiality_paise




