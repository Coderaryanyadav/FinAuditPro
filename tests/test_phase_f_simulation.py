"""Full End-to-End Simulation of Phase F Continuous Audit on ABC Manufacturing Pvt Ltd."""

from datetime import date, datetime, timezone
import pytest

from finauditpro.application.audit_adjustment_dtos import CreateAJEDTO, CreateAJELineDTO
from finauditpro.application.continuous_audit_dtos import (
    AssignAlertRequest,
    ContinuousMonitoringRunRequest,
    DataQualityRunRequest,
    UpdateInvestigationRequest,
)
from finauditpro.application.services.alert_investigation_service import AlertInvestigationService
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.continuous_audit_service import ContinuousAuditService
from finauditpro.application.services.data_quality_service import DataQualityService
from finauditpro.domain.audit_adjustment_entities import AJETypeEnum
from finauditpro.domain.continuous_audit_entities import (
    AlertSeverityEnum,
    AlertTypeEnum,
    InvestigationOutcomeEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    ContinuousAuditRepository,
    EngagementRepository,
    FirmRepository,
)


def test_abc_manufacturing_continuous_audit_simulation(tmp_path) -> None:
    """Simulates realistic continuous assurance lifecycle on ABC Manufacturing Pvt Ltd.

    Lifecycle:
    DATA INGESTION -> CONTINUOUS MONITORING -> SYSTEM SIGNAL -> AUDITOR INVESTIGATION ->
    EVIDENCE LINKING -> PROCEDURE & EXCEPTION -> AJE ADJUSTMENT -> REPORTING FINALIZATION.
    """
    db_file = tmp_path / "abc_mfg_continuous.db"
    db_manager = initialize_database(db_file)

    # 1. SETUP: Create Firm, Client, and Engagement
    with db_manager.session_scope() as session:
        firm = Firm(id="firm-abc", name="K. S. Sundaram & Co. Chartered Accountants")
        FirmRepository(session).add(firm)
        client = Client(id="client-abc", firm_id=firm.id, name="ABC Manufacturing Pvt Ltd")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-ABC-2024-25",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

    # 2. FINANCIAL DATA INGESTION: Realistic transactions for ABC Manufacturing Pvt Ltd
    transactions = [
        # Normal raw material purchase
        {
            "id": "TX-001",
            "voucher_number": "PUR-010",
            "voucher_type": "PURCHASE",
            "entry_date": "2024-06-15",
            "account_code": "5001",
            "account_name": "Steel Coil Raw Materials",
            "debit_paise": 18500000,
            "credit_paise": 0,
            "narration": "Steel coils purchase invoice JSW-881",
            "created_by_raw": "clerk_arun",
        },
        # Suspected Duplicate Invoices
        {
            "id": "TX-002",
            "voucher_number": "PUR-050",
            "voucher_type": "PURCHASE",
            "entry_date": "2024-09-10",
            "account_code": "5002",
            "account_name": "Precision Tools Supplies",
            "debit_paise": 15000000,  # ₹1,50,000
            "reference": "INV-PTS-99",
            "narration": "CNC Machine cutting tooling bits",
            "created_by_raw": "clerk_arun",
        },
        {
            "id": "TX-003",
            "voucher_number": "PUR-052",
            "entry_date": "2024-09-12",  # 2 days later, duplicate
            "account_code": "5002",
            "account_name": "Precision Tools Supplies",
            "debit_paise": 15000000,  # ₹1,50,000
            "reference": "INV-PTS-99",
            "narration": "CNC Machine cutting tooling bits duplicate entry",
            "created_by_raw": "clerk_arun",
        },
        # Period-End Manual Journal Adjustment
        {
            "id": "TX-004",
            "voucher_number": "JV-900",
            "voucher_type": "MANUAL",
            "entry_date": "2025-03-31",  # Last day of FY
            "account_code": "4001",
            "account_name": "Sales Revenue - Finished Goods",
            "debit_paise": 0,
            "credit_paise": 85000000,  # ₹8,50,000 round number
            "narration": "Year end unbilled revenue accrual adjustment",
            "created_by_raw": "admin",
        },
        # Sub-threshold Split Transactions for Transport Freight
        {
            "id": "TX-005",
            "voucher_number": "VCH-701",
            "voucher_type": "EXPENSE",
            "entry_date": "2025-01-05",
            "account_name": "Speedway Transport Carriers",
            "debit_paise": 9800000,  # ₹98,000
            "created_by_raw": "clerk_arun",
        },
        {
            "id": "TX-006",
            "voucher_number": "VCH-702",
            "voucher_type": "EXPENSE",
            "entry_date": "2025-01-06",
            "account_name": "Speedway Transport Carriers",
            "debit_paise": 9700000,  # ₹97,000
            "created_by_raw": "clerk_arun",
        },
    ]

    # 3. CONTINUOUS MONITORING: Run data quality engine and continuous monitor
    with db_manager.session_scope() as session:
        audit_repo = ContinuousAuditRepository(session)
        dq_service = DataQualityService(audit_repo=audit_repo)
        mon_service = ContinuousAuditService(audit_repo=audit_repo)
        inv_service = AlertInvestigationService(audit_repo=audit_repo)

        dq_res = dq_service.run_data_quality_checks(
            DataQualityRunRequest(engagement_id="ENG-ABC-2024-25"),
            entries_override=transactions,
        )
        assert dq_res.total_issues >= 0

        mon_summary = mon_service.monitor_transactions(
            ContinuousMonitoringRunRequest(
                engagement_id="ENG-ABC-2024-25",
                period_end_date=date(2025, 3, 31),
                approval_threshold_paise=10_00_00_00,  # ₹1 Lakh threshold
            ),
            entries_override=transactions,
        )

        assert mon_summary.transactions_monitored == 6
        assert mon_summary.alerts_generated >= 2  # Duplicate and Period-End JV flagged

        # 4. AUDITOR INVESTIGATION: Pick the duplicate transaction alert
        alerts = audit_repo.get_alerts("ENG-ABC-2024-25")
        dup_alert = [a for a in alerts if a.alert_type == AlertTypeEnum.DUPLICATE_TRANSACTION][0]

        # Assign alert to engagement auditor
        inv_service.assign_alert_to_auditor(
            AssignAlertRequest(alert_id=dup_alert.alert_id, assigned_user="ca_sundaram")
        )

        # Investigate and attach evidence: Verify duplicate invoice
        inv_res = inv_service.update_investigation(
            UpdateInvestigationRequest(
                alert_id=dup_alert.alert_id,
                auditor_id="ca_sundaram",
                status="RESOLVED",
                explanation="Voucher PUR-052 is an accidental double-booking of invoice INV-PTS-99.",
                management_response="Client acknowledges duplicate entry and requests adjustment journal entry.",
                conclusion="Confirmed duplicate purchase entry resulting in ₹1,50,000 overstatement of expenses.",
                outcome=InvestigationOutcomeEnum.VALID_FINDING.value,
                evidence_links=["EVID-INV-PTS-99-SCAN", "EVID-VENDOR-LEDGER-CONFIRMATION"],
                working_paper_ids=["WP-PURCHASE-TESTING-01"],
                procedure_ids=["PROC-SUBSTANTIVE-PURCHASES"],
                exception_ids=["EXC-PUR-DUP-01"],
                misstatement_ids=["MISST-PUR-150000"],
            )
        )
        assert inv_res.outcome == "Valid Finding"
        assert len(inv_res.evidence_links) == 2

    # 5. CREATE AUDIT ADJUSTMENT (AJE): Reverse the duplicate expense using adjustment service
    adj_service = AuditAdjustmentService(db_manager)
    aje_dto = CreateAJEDTO(
        engagement_id="ENG-ABC-2024-25",
        aje_number="AJE-001",
        entry_date="2025-03-31",
        title="Reversal of duplicate purchase booking",
        narration="Reversal of duplicate purchase booking for Precision Tools Supplies",
        reason="Duplicate invoice entry identified during continuous monitoring",
        lines=[
            CreateAJELineDTO(
                account_code="2002",
                account_name="Precision Tools Supplies (Creditors)",
                debit_paise=15000000,
                credit_paise=0,
            ),
            CreateAJELineDTO(
                account_code="5002",
                account_name="Precision Tools Supplies (Expense)",
                debit_paise=0,
                credit_paise=15000000,
            ),
        ],
        aje_type=AJETypeEnum.MANAGEMENT_ACCEPTED,
    )
    created_aje = adj_service.create_adjustment(aje_dto)
    assert created_aje.aje_number == "AJE-001"

    # 6. DASHBOARD METRICS: Ensure dashboard reflects open and confirmed items
    with db_manager.session_scope() as session:
        audit_repo = ContinuousAuditRepository(session)
        mon_service = ContinuousAuditService(audit_repo=audit_repo)
        dash = mon_service.get_dashboard_summary("ENG-ABC-2024-25")
        assert dash.alerts_generated >= 2
        assert dash.confirmed_exceptions >= 1
