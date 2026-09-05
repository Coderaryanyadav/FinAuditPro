"""Service for managing auditor investigations, evidence linking, and feedback loops on continuous alerts."""

import uuid
from datetime import UTC, datetime

from finauditpro.application.continuous_audit_dtos import (
    AlertInvestigationDto,
    AssignAlertRequest,
    RecordFeedbackRequest,
    UpdateInvestigationRequest,
)
from finauditpro.domain.continuous_audit_entities import (
    AlertInvestigation,
    AlertStatusEnum,
    AuditorFeedback,
    InvestigationOutcomeEnum,
)
from finauditpro.infrastructure.persistence.continuous_audit_models import (
    ContinuousAlertModel,
)
from finauditpro.infrastructure.persistence.repositories.continuous_audit_repository import (
    ContinuousAuditRepository,
)


class AlertInvestigationService:
    """Manages the lifecycle of converting system signals into auditor investigations and audit evidence."""

    def __init__(self, audit_repo: ContinuousAuditRepository):
        self.audit_repo = audit_repo

    def assign_alert_to_auditor(self, request: AssignAlertRequest) -> bool:
        session = self.audit_repo.session
        alert = session.get(ContinuousAlertModel, request.alert_id)
        if not alert:
            return False
        alert.assigned_user = request.assigned_user
        alert.status = AlertStatusEnum.ASSIGNED.value

        # Initialize investigation record if none exists
        existing_inv = self.audit_repo.get_investigation_by_alert(request.alert_id)
        if not existing_inv:
            inv = AlertInvestigation(
                investigation_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
                alert_id=request.alert_id,
                engagement_id=alert.engagement_id,
                auditor_id=request.assigned_user,
                status="ASSIGNED",
                outcome=InvestigationOutcomeEnum.NEEDS_INVESTIGATION,
            )
            self.audit_repo.save_investigation(inv)

        session.flush()
        return True

    def update_investigation(self, request: UpdateInvestigationRequest) -> AlertInvestigationDto:
        session = self.audit_repo.session
        existing_inv = self.audit_repo.get_investigation_by_alert(request.alert_id)
        if not existing_inv:
            alert = session.get(ContinuousAlertModel, request.alert_id)
            eng_id = alert.engagement_id if alert else "UNKNOWN"
            existing_inv = AlertInvestigation(
                investigation_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
                alert_id=request.alert_id,
                engagement_id=eng_id,
                auditor_id=request.auditor_id,
                status=request.status,
            )

        existing_inv.auditor_id = request.auditor_id
        existing_inv.status = request.status
        existing_inv.explanation = request.explanation
        existing_inv.management_response = request.management_response
        existing_inv.conclusion = request.conclusion
        existing_inv.outcome = InvestigationOutcomeEnum(request.outcome)
        existing_inv.evidence_links = request.evidence_links
        existing_inv.working_paper_ids = request.working_paper_ids
        existing_inv.procedure_ids = request.procedure_ids
        existing_inv.exception_ids = request.exception_ids
        existing_inv.misstatement_ids = request.misstatement_ids
        existing_inv.updated_at = datetime.now(UTC)

        # Update alert status based on investigation outcome
        alert = session.get(ContinuousAlertModel, request.alert_id)
        if alert:
            if existing_inv.outcome == InvestigationOutcomeEnum.FALSE_POSITIVE:
                alert.status = AlertStatusEnum.FALSE_POSITIVE.value
            elif existing_inv.outcome == InvestigationOutcomeEnum.ACCEPTED_RISK:
                alert.status = AlertStatusEnum.ACCEPTED_RISK.value
            elif existing_inv.outcome == InvestigationOutcomeEnum.VALID_FINDING:
                alert.status = AlertStatusEnum.RESOLVED.value
            else:
                alert.status = AlertStatusEnum.INVESTIGATING.value

        self.audit_repo.save_investigation(existing_inv)

        return AlertInvestigationDto(
            investigation_id=existing_inv.investigation_id,
            alert_id=existing_inv.alert_id,
            engagement_id=existing_inv.engagement_id,
            auditor_id=existing_inv.auditor_id,
            status=existing_inv.status,
            explanation=existing_inv.explanation,
            management_response=existing_inv.management_response,
            conclusion=existing_inv.conclusion,
            outcome=existing_inv.outcome.value,
            evidence_links=existing_inv.evidence_links,
            working_paper_ids=existing_inv.working_paper_ids,
            procedure_ids=existing_inv.procedure_ids,
            exception_ids=existing_inv.exception_ids,
            misstatement_ids=existing_inv.misstatement_ids,
            created_at=existing_inv.created_at.isoformat(),
            updated_at=existing_inv.updated_at.isoformat(),
        )

    def record_feedback(self, request: RecordFeedbackRequest) -> bool:
        feedback = AuditorFeedback(
            feedback_id=f"FB-{uuid.uuid4().hex[:8].upper()}",
            alert_id=request.alert_id,
            auditor_id=request.auditor_id,
            was_useful=request.was_useful,
            is_false_positive=request.is_false_positive,
            is_actual_exception=request.is_actual_exception,
            is_misstatement=request.is_misstatement,
            procedure_created=request.procedure_created,
            comments=request.comments,
        )
        self.audit_repo.save_feedback(feedback)
        return True

    def get_alert_explainability(self, alert_id: str) -> dict:
        alert = self.audit_repo.get_alert_by_id(alert_id)
        if not alert:
            return {}

        return {
            "alert_id": alert.alert_id,
            "rule_version": alert.model_rule_version,
            "is_experimental": alert.is_experimental,
            "status": alert.status.value,
            "assigned_user": alert.assigned_user,
            "risk_score": alert.risk_score,
            "contributing_factors": [
                {
                    "factor": f.factor_name,
                    "points": f.score_contribution,
                    "explanation": f.description,
                }
                for f in alert.risk_factors
            ],
            "input_data": alert.affected_data,
            "human_review_status": "Reviewed by Auditor" if alert.status != AlertStatusEnum.NEW else "Awaiting Auditor Investigation",
            "statutory_caveat": (
                "This signal is an automated system detection intended to guide professional auditor inquiry. "
                "It does not represent a conclusion of non-compliance, error, or statutory finding."
            ),
        }
