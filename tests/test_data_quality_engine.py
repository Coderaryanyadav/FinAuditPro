"""Unit tests for the deterministic Data Quality Engine and DataQualityService."""

from datetime import date, datetime, timezone
import pytest

from finauditpro.application.continuous_audit_dtos import DataQualityRunRequest
from finauditpro.application.services.data_quality_service import DataQualityService
from finauditpro.domain.continuous_audit_entities import (
    DataQualitySeverityEnum,
    DataQualityTypeEnum,
)
from finauditpro.domain.data_quality_engine import DataQualityEngine
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.continuous_audit_models import DataQualityIssueModel
from finauditpro.infrastructure.persistence.repositories.continuous_audit_repository import (
    ContinuousAuditRepository,
)


def test_data_quality_engine_detects_all_anomalies() -> None:
    engine = DataQualityEngine()
    eval_date = date(2025, 3, 31)

    entries = [
        # 1. Negative Dr/Cr sign
        {
            "id": "ROW-1",
            "voucher_number": "V1",
            "entry_date": "2025-01-15",
            "account_code": "1001",
            "account_name": "Cash",
            "debit_paise": -5000,
            "credit_paise": 0,
            "narration": "Negative entry",
            "created_by_raw": "user1",
        },
        # 2. Missing Account
        {
            "id": "ROW-2",
            "voucher_number": "V2",
            "entry_date": "2025-01-16",
            "account_code": "",
            "account_name": "",
            "debit_paise": 5000,
            "credit_paise": 0,
            "narration": "Missing account info",
            "created_by_raw": "user1",
        },
        # 3. Invalid Account Reference (not in known list)
        {
            "id": "ROW-3",
            "voucher_number": "V3",
            "entry_date": "2025-01-17",
            "account_code": "9999",
            "account_name": "Unknown Ghost Account",
            "debit_paise": 5000,
            "credit_paise": 0,
            "narration": "Ghost account reference",
            "created_by_raw": "user1",
        },
        # 4. Missing Description & Missing User
        {
            "id": "ROW-4",
            "voucher_number": "V4",
            "entry_date": "2025-01-18",
            "account_code": "1001",
            "account_name": "Cash",
            "debit_paise": 5000,
            "credit_paise": 0,
            "narration": "",
            "created_by_raw": "",
        },
        # 5. Future-dated entry
        {
            "id": "ROW-5",
            "voucher_number": "V5",
            "entry_date": "2026-06-01",
            "account_code": "1001",
            "account_name": "Cash",
            "debit_paise": 5000,
            "credit_paise": 0,
            "narration": "Future transaction",
            "created_by_raw": "user1",
        },
        # 6. Unbalanced Voucher V6
        {
            "id": "ROW-6A",
            "voucher_number": "V6",
            "entry_date": "2025-02-01",
            "account_code": "1001",
            "account_name": "Cash",
            "debit_paise": 10000,
            "credit_paise": 0,
            "narration": "Dr line",
            "created_by_raw": "user1",
        },
        {
            "id": "ROW-6B",
            "voucher_number": "V6",
            "entry_date": "2025-02-01",
            "account_code": "2001",
            "account_name": "Vendor A",
            "debit_paise": 0,
            "credit_paise": 8000,
            "narration": "Cr line unbalanced",
            "created_by_raw": "user1",
        },
        # 7. Cross-engagement reference leak
        {
            "id": "ROW-7",
            "engagement_id": "ENG-OTHER",
            "voucher_number": "V7",
            "entry_date": "2025-02-02",
            "account_code": "1001",
            "account_name": "Cash",
            "debit_paise": 5000,
            "credit_paise": 5000,
            "narration": "Foreign tenant leak",
            "created_by_raw": "user1",
        },
    ]

    known_accounts = {"1001", "2001", "3001"}
    issues = engine.evaluate_ledger_entries(
        engagement_id="ENG-TARGET",
        dataset_id="DS-1",
        entries=entries,
        known_account_codes=known_accounts,
        period_start=date(2024, 4, 1),
        period_end=date(2025, 3, 31),
        as_of_date=eval_date,
    )

    issue_types = {i.issue_type for i in issues}
    assert DataQualityTypeEnum.INVALID_DEBIT_CREDIT_SIGN in issue_types
    assert DataQualityTypeEnum.MISSING_ACCOUNT in issue_types
    assert DataQualityTypeEnum.INVALID_ACCOUNT_REF in issue_types
    assert DataQualityTypeEnum.MISSING_DESCRIPTION in issue_types
    assert DataQualityTypeEnum.MISSING_USER in issue_types
    assert DataQualityTypeEnum.FUTURE_DATED in issue_types
    assert DataQualityTypeEnum.UNBALANCED_JOURNAL in issue_types
    assert DataQualityTypeEnum.CROSS_ENGAGEMENT_REF in issue_types


def test_data_quality_service_persistence_and_resolution(tmp_path) -> None:
    db_file = tmp_path / "dq_test.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        from finauditpro.domain.entities import AuditTypeEnum, Client, Engagement, EngagementStatusEnum, Firm
        from finauditpro.infrastructure.persistence.repositories import ClientRepository, EngagementRepository, FirmRepository

        firm = Firm(id="firm-test", name="Test Firm")
        FirmRepository(session).add(firm)
        client = Client(id="client-test", firm_id=firm.id, name="Test Client")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-TEST",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)
        session.flush()

        repo = ContinuousAuditRepository(session)
        service = DataQualityService(audit_repo=repo)

        req = DataQualityRunRequest(engagement_id="ENG-TEST")
        sample_entries = [
            {
                "id": "T1",
                "voucher_number": "JV-99",
                "entry_date": "2025-01-10",
                "account_code": "1001",
                "account_name": "Cash",
                "debit_paise": 5000,
                "credit_paise": 0,
                "narration": "Line 1",
                "created_by_raw": "auditor",
            },
            {
                "id": "T2",
                "voucher_number": "JV-99",
                "entry_date": "2025-01-10",
                "account_code": "2001",
                "account_name": "Payable",
                "debit_paise": 0,
                "credit_paise": 3000,  # Unbalanced
                "narration": "Line 2",
                "created_by_raw": "auditor",
            },
        ]

        result = service.run_data_quality_checks(req, entries_override=sample_entries)
        assert result.total_issues > 0
        assert result.critical_count >= 1

        unbalanced_issue = [i for i in result.issues if i.issue_type == "Unbalanced Journal"][0]
        assert unbalanced_issue.issue_id is not None

        # Test resolving the issue
        res_ok = service.resolve_data_quality_issue(
            issue_id=unbalanced_issue.issue_id,
            resolution="Corrected voucher line in ERP ledger",
            resolved_by="Senior Auditor",
        )
        assert res_ok is True

        stored = session.get(DataQualityIssueModel, unbalanced_issue.issue_id)
        assert stored.resolution == "Corrected voucher line in ERP ledger"
        assert stored.resolved_by == "Senior Auditor"
        assert stored.resolved_at is not None
