"""Repository for storing and querying continuous audit alerts, data quality issues, and investigations."""

from datetime import datetime, timezone
import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.continuous_audit_entities import (
    AlertInvestigation,
    AlertSeverityEnum,
    AlertStatusEnum,
    AlertTypeEnum,
    AuditorFeedback,
    ContinuousAlert,
    DataQualityIssue,
    DataQualitySeverityEnum,
    DataQualityTypeEnum,
    InvestigationOutcomeEnum,
    RiskFactorContribution,
)
from finauditpro.infrastructure.persistence.continuous_audit_models import (
    AlertFeedbackModel,
    AlertInvestigationModel,
    ContinuousAlertModel,
    ContinuousReconciliationRecordModel,
    DataQualityIssueModel,
)


class ContinuousAuditRepository:
    """Handles database persistence for Phase F continuous assurance records."""

    def __init__(self, session: Session):
        self.session = session

    # --- DATA QUALITY ISSUES ---
    def save_data_quality_issues(self, issues: list[DataQualityIssue]) -> None:
        for issue in issues:
            model = DataQualityIssueModel(
                id=issue.issue_id,
                engagement_id=issue.engagement_id,
                dataset_id=issue.dataset_id,
                issue_type=issue.issue_type.value,
                severity=issue.severity.value,
                source=issue.source,
                description=issue.description,
                affected_records_json=json.dumps(issue.affected_records),
                resolution=issue.resolution,
                resolved_by=issue.resolved_by,
                resolved_at=issue.resolved_at.isoformat() if issue.resolved_at else None,
                detected_at=issue.detected_at.isoformat(),
            )
            self.session.add(model)
        self.session.flush()

    def get_data_quality_issues(
        self, engagement_id: str, severity: Optional[str] = None
    ) -> list[DataQualityIssue]:
        stmt = select(DataQualityIssueModel).where(DataQualityIssueModel.engagement_id == engagement_id)
        if severity:
            stmt = stmt.where(DataQualityIssueModel.severity == severity)
        models = self.session.execute(stmt).scalars().all()
        results: list[DataQualityIssue] = []
        for m in models:
            results.append(
                DataQualityIssue(
                    issue_id=m.id,
                    engagement_id=m.engagement_id,
                    dataset_id=m.dataset_id,
                    issue_type=DataQualityTypeEnum(m.issue_type),
                    severity=DataQualitySeverityEnum(m.severity),
                    source=m.source,
                    detected_at=datetime.fromisoformat(m.detected_at),
                    affected_records=json.loads(m.affected_records_json or "[]"),
                    description=m.description,
                    resolution=m.resolution,
                    resolved_by=m.resolved_by,
                    resolved_at=datetime.fromisoformat(m.resolved_at) if m.resolved_at else None,
                )
            )
        return results

    # --- CONTINUOUS ALERTS ---
    def save_alerts(self, alerts: list[ContinuousAlert]) -> list[ContinuousAlert]:
        saved: list[ContinuousAlert] = []
        for alert in alerts:
            # Check deduplication hash to prevent alert fatigue
            if alert.dedup_hash:
                existing = self.session.execute(
                    select(ContinuousAlertModel).where(
                        ContinuousAlertModel.engagement_id == alert.engagement_id,
                        ContinuousAlertModel.dedup_hash == alert.dedup_hash,
                    )
                ).scalars().first()
                if existing:
                    # Suppress or update existing rather than flooding auditor
                    alert.suppressed = True
                    alert.suppression_reason = f"Duplicate alert signature matches active alert {existing.id}."
                    continue

            factors_json = json.dumps([
                {"factor_name": f.factor_name, "score_contribution": f.score_contribution, "description": f.description}
                for f in alert.risk_factors
            ])

            model = ContinuousAlertModel(
                id=alert.alert_id,
                engagement_id=alert.engagement_id,
                alert_type=alert.alert_type.value,
                severity=alert.severity.value,
                title=alert.title,
                description=alert.description,
                source=alert.source,
                risk_score=alert.risk_score,
                risk_factors_json=factors_json,
                affected_data_json=json.dumps(alert.affected_data),
                status=alert.status.value,
                assigned_user=alert.assigned_user,
                dedup_hash=alert.dedup_hash,
                suppressed=1 if alert.suppressed else 0,
                suppression_reason=alert.suppression_reason,
                is_experimental=1 if alert.is_experimental else 0,
                model_rule_version=alert.model_rule_version,
                detected_at=alert.detected_at.isoformat(),
            )
            self.session.add(model)
            saved.append(alert)

        self.session.flush()
        return saved

    def get_alerts(
        self,
        engagement_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        include_suppressed: bool = False,
    ) -> list[ContinuousAlert]:
        stmt = select(ContinuousAlertModel).where(ContinuousAlertModel.engagement_id == engagement_id)
        if status:
            stmt = stmt.where(ContinuousAlertModel.status == status)
        if severity:
            stmt = stmt.where(ContinuousAlertModel.severity == severity)
        if not include_suppressed:
            stmt = stmt.where(ContinuousAlertModel.suppressed == 0)

        models = self.session.execute(stmt).scalars().all()
        results: list[ContinuousAlert] = []
        for m in models:
            raw_factors = json.loads(m.risk_factors_json or "[]")
            factors = [
                RiskFactorContribution(
                    factor_name=f["factor_name"],
                    score_contribution=f["score_contribution"],
                    description=f["description"],
                )
                for f in raw_factors
            ]
            results.append(
                ContinuousAlert(
                    alert_id=m.id,
                    engagement_id=m.engagement_id,
                    alert_type=AlertTypeEnum(m.alert_type),
                    severity=AlertSeverityEnum(m.severity),
                    title=m.title,
                    description=m.description,
                    source=m.source,
                    detected_at=datetime.fromisoformat(m.detected_at),
                    affected_data=json.loads(m.affected_data_json or "{}"),
                    risk_score=m.risk_score,
                    risk_factors=factors,
                    status=AlertStatusEnum(m.status),
                    assigned_user=m.assigned_user,
                    dedup_hash=m.dedup_hash,
                    suppressed=bool(m.suppressed),
                    suppression_reason=m.suppression_reason,
                    is_experimental=bool(m.is_experimental),
                    model_rule_version=m.model_rule_version,
                )
            )
        return results

    def get_alert_by_id(self, alert_id: str) -> Optional[ContinuousAlert]:
        m = self.session.get(ContinuousAlertModel, alert_id)
        if not m:
            return None
        raw_factors = json.loads(m.risk_factors_json or "[]")
        factors = [
            RiskFactorContribution(
                factor_name=f["factor_name"],
                score_contribution=f["score_contribution"],
                description=f["description"],
            )
            for f in raw_factors
        ]
        return ContinuousAlert(
            alert_id=m.id,
            engagement_id=m.engagement_id,
            alert_type=AlertTypeEnum(m.alert_type),
            severity=AlertSeverityEnum(m.severity),
            title=m.title,
            description=m.description,
            source=m.source,
            detected_at=datetime.fromisoformat(m.detected_at),
            affected_data=json.loads(m.affected_data_json or "{}"),
            risk_score=m.risk_score,
            risk_factors=factors,
            status=AlertStatusEnum(m.status),
            assigned_user=m.assigned_user,
            dedup_hash=m.dedup_hash,
            suppressed=bool(m.suppressed),
            suppression_reason=m.suppression_reason,
            is_experimental=bool(m.is_experimental),
            model_rule_version=m.model_rule_version,
        )

    # --- INVESTIGATIONS ---
    def save_investigation(self, inv: AlertInvestigation) -> AlertInvestigation:
        m = self.session.get(AlertInvestigationModel, inv.investigation_id)
        if not m:
            m = AlertInvestigationModel(
                id=inv.investigation_id,
                alert_id=inv.alert_id,
                engagement_id=inv.engagement_id,
                auditor_id=inv.auditor_id,
            )
            self.session.add(m)

        m.status = inv.status
        m.evidence_links_json = json.dumps(inv.evidence_links)
        m.working_paper_ids_json = json.dumps(inv.working_paper_ids)
        m.procedure_ids_json = json.dumps(inv.procedure_ids)
        m.exception_ids_json = json.dumps(inv.exception_ids)
        m.misstatement_ids_json = json.dumps(inv.misstatement_ids)
        m.explanation = inv.explanation
        m.management_response = inv.management_response
        m.conclusion = inv.conclusion
        m.outcome = inv.outcome.value
        m.updated_at = datetime.now(timezone.utc).isoformat()
        self.session.flush()
        return inv

    def get_investigation_by_alert(self, alert_id: str) -> Optional[AlertInvestigation]:
        stmt = select(AlertInvestigationModel).where(AlertInvestigationModel.alert_id == alert_id)
        m = self.session.execute(stmt).scalars().first()
        if not m:
            return None
        return AlertInvestigation(
            investigation_id=m.id,
            alert_id=m.alert_id,
            engagement_id=m.engagement_id,
            auditor_id=m.auditor_id,
            status=m.status,
            evidence_links=json.loads(m.evidence_links_json or "[]"),
            working_paper_ids=json.loads(m.working_paper_ids_json or "[]"),
            procedure_ids=json.loads(m.procedure_ids_json or "[]"),
            exception_ids=json.loads(m.exception_ids_json or "[]"),
            misstatement_ids=json.loads(m.misstatement_ids_json or "[]"),
            explanation=m.explanation,
            management_response=m.management_response,
            conclusion=m.conclusion,
            outcome=InvestigationOutcomeEnum(m.outcome),
            created_at=datetime.fromisoformat(m.created_at),
            updated_at=datetime.fromisoformat(m.updated_at),
        )

    # --- FEEDBACK ---
    def save_feedback(self, fb: AuditorFeedback) -> AuditorFeedback:
        m = AlertFeedbackModel(
            id=fb.feedback_id,
            alert_id=fb.alert_id,
            auditor_id=fb.auditor_id,
            was_useful=1 if fb.was_useful else 0,
            is_false_positive=1 if fb.is_false_positive else 0,
            is_actual_exception=1 if fb.is_actual_exception else 0,
            is_misstatement=1 if fb.is_misstatement else 0,
            procedure_created=1 if fb.procedure_created else 0,
            comments=fb.comments,
            recorded_at=fb.recorded_at.isoformat(),
        )
        self.session.add(m)
        self.session.flush()
        return fb
