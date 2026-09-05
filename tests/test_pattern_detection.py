"""Unit tests for Pattern Detection Engine: Duplicates, Split Transactions, and Control Monitoring."""


from finauditpro.domain.continuous_audit_entities import AlertSeverityEnum, AlertTypeEnum
from finauditpro.domain.pattern_detection_engine import PatternDetectionEngine


def test_duplicate_transaction_detection() -> None:
    engine = PatternDetectionEngine()

    txns = [
        {
            "id": "TX-1",
            "voucher_number": "V-100",
            "entry_date": "2025-01-10",
            "account_name": "Acme Industrial Supplies",
            "debit_paise": 12500000,  # ₹1,25,000
            "reference": "INV-2025-09",
        },
        {
            "id": "TX-2",
            "voucher_number": "V-105",
            "entry_date": "2025-01-12",  # 2 days later
            "account_name": "Acme Industrial Supplies",
            "debit_paise": 12500000,  # Identical amount
            "reference": "INV-2025-09",  # Identical reference
        },
        {
            "id": "TX-3",
            "voucher_number": "V-110",
            "entry_date": "2025-01-20",
            "account_name": "Zenith Consulting",
            "debit_paise": 8500000,
            "reference": "INV-ZEN-01",
        },
    ]

    alerts = engine.detect_duplicate_transactions("ENG-1", txns, date_window_days=5)
    assert len(alerts) == 1
    dup_alert = alerts[0]
    assert dup_alert.alert_type == AlertTypeEnum.DUPLICATE_TRANSACTION
    assert "ACME INDUSTRIAL SUPPLIES" in dup_alert.title.upper()
    assert dup_alert.risk_score >= 70.0
    assert "TX-1" in dup_alert.affected_data["record_ids"]
    assert "TX-2" in dup_alert.affected_data["record_ids"]


def test_split_transaction_detection() -> None:
    # Threshold = ₹1,00,000 (10,000,000 paise)
    engine = PatternDetectionEngine(approval_threshold_paise=10_00_00_00)

    # 3 sub-threshold transactions clustered within 5 days
    txns = [
        {
            "id": "TX-A",
            "voucher_number": "V-201",
            "entry_date": "2025-02-01",
            "account_name": "Apex Logistics Pvt Ltd",
            "debit_paise": 9800000,  # ₹98,000
            "created_by_raw": "purchaser_1",
        },
        {
            "id": "TX-B",
            "voucher_number": "V-202",
            "entry_date": "2025-02-02",
            "account_name": "Apex Logistics Pvt Ltd",
            "debit_paise": 9750000,  # ₹97,500
            "created_by_raw": "purchaser_1",
        },
        {
            "id": "TX-C",
            "voucher_number": "V-203",
            "entry_date": "2025-02-04",
            "account_name": "Apex Logistics Pvt Ltd",
            "debit_paise": 9900000,  # ₹99,000
            "created_by_raw": "purchaser_1",
        },
    ]

    alerts = engine.detect_split_transactions("ENG-1", txns, window_days=7)
    assert len(alerts) >= 1
    split_alert = alerts[0]
    assert split_alert.alert_type == AlertTypeEnum.SPLIT_TRANSACTION
    assert "Sub-Threshold Transaction Splitting" in split_alert.title
    assert "APEX LOGISTICS PVT LTD" in split_alert.affected_data["party_name"].upper()
    assert split_alert.affected_data["aggregate_amount_paise"] == (9800000 + 9750000 + 9900000)
    assert split_alert.affected_data["aggregate_amount_paise"] > 10_00_00_00


def test_control_monitoring_evaluations() -> None:
    engine = PatternDetectionEngine()

    # 1. Maker == Reviewer
    sod_alerts = engine.evaluate_control_monitoring(
        engagement_id="ENG-1",
        action_type="Approve Journal Voucher",
        maker_id="auditor_rajesh",
        reviewer_id="auditor_rajesh",
    )
    assert len(sod_alerts) == 1
    assert sod_alerts[0].alert_type == AlertTypeEnum.CONTROL_VIOLATION
    assert sod_alerts[0].severity == AlertSeverityEnum.CRITICAL
    assert "Maker and Reviewer Are Identical" in sod_alerts[0].title

    # 2. Mutating a locked engagement
    lock_alerts = engine.evaluate_control_monitoring(
        engagement_id="ENG-1",
        action_type="Post Adjustment Journal",
        maker_id="partner_arun",
        reviewer_id="partner_arun",
        is_engagement_locked=True,
    )
    # Both SOD and Locked breach triggers
    types = {a.title for a in lock_alerts}
    assert any("Locked Engagement" in t for t in types)
