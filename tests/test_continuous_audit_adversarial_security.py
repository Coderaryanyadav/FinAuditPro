"""Adversarial and security tests for continuous audit engine: evasion resistance and tenant isolation."""

from datetime import date

from finauditpro.application.continuous_audit_dtos import ContinuousMonitoringRunRequest
from finauditpro.application.services.continuous_audit_service import ContinuousAuditService
from finauditpro.domain.continuous_audit_entities import AlertSeverityEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
)
from finauditpro.domain.pattern_detection_engine import PatternDetectionEngine
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    ContinuousAuditRepository,
    EngagementRepository,
    FirmRepository,
)


def test_adversarial_duplicate_with_altered_description() -> None:
    """Tests that altering transaction descriptions does not evade duplicate detection when vendor and amount match within window."""
    engine = PatternDetectionEngine()

    txns = [
        {
            "id": "TX-ORIG",
            "voucher_number": "V-10",
            "entry_date": "2025-02-10",
            "account_name": "Dynamic Infotech Services",
            "debit_paise": 4500000,  # ₹45,000
            "reference": "INV-100",
            "narration": "Cloud hosting services February",
        },
        {
            "id": "TX-EVADED",
            "voucher_number": "V-15",
            "entry_date": "2025-02-12",  # 2 days later
            "account_name": "Dynamic Infotech Services",
            "debit_paise": 4500000,  # Identical amount
            "reference": "INV-100-ALT",  # Altered reference
            "narration": "Server infrastructure maintenance charges",  # Altered description
        },
    ]

    alerts = engine.detect_duplicate_transactions("ENG-1", txns, date_window_days=5)
    assert len(alerts) == 1
    assert "DYNAMIC INFOTECH SERVICES" in alerts[0].title.upper()
    assert alerts[0].risk_score >= 60.0


def test_adversarial_multi_tenant_isolation(tmp_path) -> None:
    """Verifies strict cross-engagement tenant isolation for continuous alerts and investigations."""
    db_file = tmp_path / "tenant_iso_test.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm = Firm(id="firm-iso", name="Isolation Firm")
        FirmRepository(session).add(firm)

        # Client & Engagement 1 (Tenant Alpha)
        client_a = Client(id="client-a", firm_id=firm.id, name="Client Alpha")
        ClientRepository(session).add(client_a)
        eng_a = Engagement(
            id="ENG-ALPHA",
            firm_id=firm.id,
            client_id=client_a.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng_a)

        # Client & Engagement 2 (Tenant Beta)
        client_b = Client(id="client-b", firm_id=firm.id, name="Client Beta")
        ClientRepository(session).add(client_b)
        eng_b = Engagement(
            id="ENG-BETA",
            firm_id=firm.id,
            client_id=client_b.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng_b)
        session.flush()

        repo = ContinuousAuditRepository(session)
        service = ContinuousAuditService(audit_repo=repo)

        # Ingest alert for Alpha
        entry_alpha = [{
            "id": "T-ALPHA",
            "voucher_number": "JV-A",
            "voucher_type": "MANUAL",
            "entry_date": "2025-03-31",
            "account_code": "1001",
            "account_name": "Cash",
            "debit_paise": 10000000,
            "credit_paise": 0,
            "narration": "Alpha year end manual entry",
            "created_by_raw": "admin",
        }]
        service.monitor_transactions(
            ContinuousMonitoringRunRequest(engagement_id="ENG-ALPHA", period_end_date=date(2025, 3, 31)),
            entries_override=entry_alpha,
        )

        # Query Beta: MUST be completely isolated (zero alerts returned)
        beta_alerts = repo.get_alerts("ENG-BETA")
        assert len(beta_alerts) == 0

        # Query Alpha: Exactly 1 alert returned
        alpha_alerts = repo.get_alerts("ENG-ALPHA")
        assert len(alpha_alerts) == 1
        assert alpha_alerts[0].engagement_id == "ENG-ALPHA"


def test_adversarial_locked_engagement_control_exception() -> None:
    """Verifies that attempts to mutate finalized/locked engagement trigger critical control exception."""
    engine = PatternDetectionEngine()

    alerts = engine.evaluate_control_monitoring(
        engagement_id="ENG-LOCKED",
        action_type="Post Adjustment Journal Entry",
        maker_id="auditor_subhash",
        reviewer_id="auditor_subhash",
        is_engagement_locked=True,
    )

    crit_alerts = [a for a in alerts if a.severity == AlertSeverityEnum.CRITICAL]
    assert len(crit_alerts) >= 1
    assert any("Modification Attempted on Locked Engagement" in a.title for a in crit_alerts)
