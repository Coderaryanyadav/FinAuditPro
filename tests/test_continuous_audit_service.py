"""Integration tests for ContinuousAuditService, alert fatigue control, and reconciliations."""

from datetime import date, datetime, timezone
import pytest

from finauditpro.application.continuous_audit_dtos import ContinuousMonitoringRunRequest
from finauditpro.application.services.continuous_audit_service import ContinuousAuditService
from finauditpro.domain.continuous_audit_entities import AlertSeverityEnum, AlertTypeEnum
from finauditpro.domain.entities import AuditTypeEnum, Client, Engagement, EngagementStatusEnum, Firm
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    ContinuousAuditRepository,
    EngagementRepository,
    FirmRepository,
)


def test_continuous_monitoring_and_fatigue_deduplication(tmp_path) -> None:
    db_file = tmp_path / "cas_test.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm = Firm(id="firm-cas", name="CAS Firm")
        FirmRepository(session).add(firm)
        client = Client(id="client-cas", firm_id=firm.id, name="CAS Client")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-CAS",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)
        session.flush()

        repo = ContinuousAuditRepository(session)
        service = ContinuousAuditService(audit_repo=repo)

        req = ContinuousMonitoringRunRequest(
            engagement_id="ENG-CAS",
            period_end_date=date(2025, 3, 31),
        )

        entries = [
            {
                "id": "T1",
                "voucher_number": "JV-500",
                "voucher_type": "MANUAL",
                "entry_date": "2025-03-30",  # Sunday, period end
                "account_code": "1001",
                "account_name": "Cash In Hand",
                "debit_paise": 10000000,  # Round 1 Lakh
                "credit_paise": 0,
                "narration": "Year end cash adjustment",
                "created_by_raw": "admin",
            }
        ]

        # First run: alert generated and saved
        summary1 = service.monitor_transactions(req, entries_override=entries)
        assert summary1.alerts_generated == 1
        assert summary1.suppressed_alerts == 0

        # Second run with identical entries: alert fatigue suppression prevents duplicate alert
        summary2 = service.monitor_transactions(req, entries_override=entries)
        assert summary2.alerts_generated == 0
        assert summary2.suppressed_alerts == 1

        # Check dashboard
        dashboard = service.get_dashboard_summary("ENG-CAS")
        assert dashboard.alerts_generated == 1
        assert dashboard.high_risk_signals >= 1


def test_continuous_reconciliation_tb_and_subledgers(tmp_path) -> None:
    db_file = tmp_path / "recon_test.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm = Firm(id="firm-recon", name="Recon Firm")
        FirmRepository(session).add(firm)
        client = Client(id="client-recon", firm_id=firm.id, name="Recon Client")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-RECON",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)
        session.flush()

        repo = ContinuousAuditRepository(session)
        service = ContinuousAuditService(audit_repo=repo)

        tb_lines = [
            {"account_code": "1001", "debit_paise": 500000, "credit_paise": 0},
            {"account_code": "2001", "debit_paise": 0, "credit_paise": 500000},
        ]
        subledgers = {
            "Debtors": (500000, 500000),  # Balanced
            "Creditors": (500000, 480000),  # Discrepancy
        }

        records = service.run_continuous_reconciliation("ENG-RECON", tb_lines, subledgers=subledgers)
        assert len(records) == 3

        tb_rec = [r for r in records if r.reconciliation_type == "TB_BALANCE"][0]
        assert tb_rec.status == "BALANCED"

        debtors_rec = [r for r in records if "DEBTORS" in r.reconciliation_type][0]
        assert debtors_rec.status == "BALANCED"

        creditors_rec = [r for r in records if "CREDITORS" in r.reconciliation_type][0]
        assert creditors_rec.status == "DISCREPANCY"
        assert creditors_rec.difference_paise == 20000
