"""Unit tests for AlertInvestigationService: investigation workflow, evidence linking, and explainability."""

from datetime import UTC, datetime

from finauditpro.application.continuous_audit_dtos import (
    AssignAlertRequest,
    RecordFeedbackRequest,
    UpdateInvestigationRequest,
)
from finauditpro.application.services.alert_investigation_service import AlertInvestigationService
from finauditpro.domain.continuous_audit_entities import (
    AlertSeverityEnum,
    AlertStatusEnum,
    AlertTypeEnum,
    ContinuousAlert,
    InvestigationOutcomeEnum,
    RiskFactorContribution,
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


def test_alert_investigation_lifecycle_and_evidence_linking(tmp_path) -> None:
    db_file = tmp_path / "inv_test.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm = Firm(id="firm-inv", name="Inv Firm")
        FirmRepository(session).add(firm)
        client = Client(id="client-inv", firm_id=firm.id, name="Inv Client")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-INV",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)
        session.flush()

        repo = ContinuousAuditRepository(session)
        inv_service = AlertInvestigationService(audit_repo=repo)

        # 1. Create a system alert
        alert = ContinuousAlert(
            alert_id="ALT-100",
            engagement_id="ENG-INV",
            alert_type=AlertTypeEnum.UNUSUAL_TRANSACTION,
            severity=AlertSeverityEnum.HIGH,
            title="Potential Risk Signal: High-Value Manual JV",
            description="Manual JV posted on weekend",
            source="Continuous JE Monitor",
            detected_at=datetime.now(UTC),
            affected_data={"voucher_number": "JV-100", "amount_paise": 50000000},
            risk_score=75.0,
            risk_factors=[
                RiskFactorContribution(
                    factor_name="Manual Journal Entry",
                    score_contribution=25.0,
                    description="Manual adjustment",
                ),
                RiskFactorContribution(
                    factor_name="High-Value Transaction",
                    score_contribution=50.0,
                    description="Amount exceeds 50 Lakhs",
                ),
            ],
            dedup_hash="SIG-100",
        )
        repo.save_alerts([alert])

        # 2. Assign to Auditor
        assign_ok = inv_service.assign_alert_to_auditor(
            AssignAlertRequest(alert_id="ALT-100", assigned_user="ca_ananya")
        )
        assert assign_ok is True
        fetched_alert = repo.get_alert_by_id("ALT-100")
        assert fetched_alert.status == AlertStatusEnum.ASSIGNED
        assert fetched_alert.assigned_user == "ca_ananya"

        # 3. Auditor performs investigation and links evidence & procedures
        update_req = UpdateInvestigationRequest(
            alert_id="ALT-100",
            auditor_id="ca_ananya",
            status="RESOLVED",
            explanation="Inspected underlying bank statement and board resolution approving year-end provision.",
            management_response="Confirmed provision approved by Audit Committee on March 28.",
            conclusion="Properly authorized under Companies Act Section 177. No adjustment required.",
            outcome=InvestigationOutcomeEnum.VALID_FINDING.value,
            evidence_links=["EVID-BANK-STMT-PAGE-12", "EVID-BOARD-MINUTES-DOC-4"],
            working_paper_ids=["WP-PROVISIONS-01"],
            procedure_ids=["PROC-SUBST-PROVISIONS-03"],
        )
        inv_dto = inv_service.update_investigation(update_req)
        assert inv_dto.outcome == "Valid Finding"
        assert len(inv_dto.evidence_links) == 2
        assert "WP-PROVISIONS-01" in inv_dto.working_paper_ids

        # 4. Record Auditor Feedback
        fb_ok = inv_service.record_feedback(
            RecordFeedbackRequest(
                alert_id="ALT-100",
                auditor_id="ca_ananya",
                was_useful=True,
                is_false_positive=False,
                is_actual_exception=False,
                is_misstatement=False,
                procedure_created=True,
                comments="Signal successfully highlighted material adjustment requiring board inquiry.",
            )
        )
        assert fb_ok is True

        # 5. Verify Explainability
        expl = inv_service.get_alert_explainability("ALT-100")
        assert expl["alert_id"] == "ALT-100"
        assert expl["risk_score"] == 75.0
        assert len(expl["contributing_factors"]) == 2
        assert "statutory_caveat" in expl
        assert "does not represent a conclusion" in expl["statutory_caveat"]
