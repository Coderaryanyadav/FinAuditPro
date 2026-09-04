"""Central continuous audit service orchestrating anomaly monitoring, alert fatigue control, and dashboard metrics."""

from datetime import datetime, timezone
import json
from typing import Any, Optional

from sqlalchemy import select

from finauditpro.application.continuous_audit_dtos import (
    ContinuousAlertDto,
    ContinuousAuditDashboardDto,
    ContinuousMonitoringRunRequest,
    ContinuousMonitoringSummaryDto,
    RiskFactorContributionDto,
)
from finauditpro.domain.continuous_audit_entities import (
    AlertSeverityEnum,
    AlertStatusEnum,
    ContinuousAlert,
)
from finauditpro.domain.continuous_reconciliation_engine import (
    ContinuousReconciliationEngine,
)
from finauditpro.domain.journal_analytics_engine import JournalAnalyticsEngine
from finauditpro.domain.pattern_detection_engine import PatternDetectionEngine
from finauditpro.infrastructure.persistence.continuous_audit_models import (
    AlertInvestigationModel,
    ContinuousAlertModel,
    ContinuousReconciliationRecordModel,
    DataQualityIssueModel,
)
from finauditpro.infrastructure.persistence.repositories.continuous_audit_repository import (
    ContinuousAuditRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import (
    FinancialDataRepository,
)


class ContinuousAuditService:
    """Orchestrates transaction ingestion, deterministic risk evaluation, alert deduplication, and dashboards."""

    def __init__(
        self,
        audit_repo: ContinuousAuditRepository,
        financial_repo: Optional[FinancialDataRepository] = None,
        journal_engine: Optional[JournalAnalyticsEngine] = None,
        pattern_engine: Optional[PatternDetectionEngine] = None,
        recon_engine: Optional[ContinuousReconciliationEngine] = None,
    ):
        self.audit_repo = audit_repo
        self.financial_repo = financial_repo
        self.journal_engine = journal_engine or JournalAnalyticsEngine()
        self.pattern_engine = pattern_engine or PatternDetectionEngine()
        self.recon_engine = recon_engine or ContinuousReconciliationEngine()

    def monitor_transactions(
        self,
        request: ContinuousMonitoringRunRequest,
        entries_override: Optional[list[dict[str, Any]]] = None,
    ) -> ContinuousMonitoringSummaryDto:
        entries: list[dict[str, Any]] = []

        if entries_override is not None:
            entries = entries_override
        elif self.financial_repo and request.dataset_id:
            db_entries = self.financial_repo.get_ledger_entries(request.dataset_id)
            for e in db_entries:
                entries.append({
                    "id": e.id,
                    "dataset_id": e.dataset_id,
                    "voucher_number": e.voucher_number,
                    "voucher_type": e.voucher_type,
                    "entry_date": e.entry_date,
                    "account_code": e.account_code,
                    "account_name": e.account_name,
                    "debit_paise": e.debit_paise,
                    "credit_paise": e.credit_paise,
                    "narration": e.narration,
                    "reference": e.reference,
                    "created_by_raw": e.created_by_raw,
                })

        if request.period_end_date:
            self.journal_engine.period_end_date = request.period_end_date
        if request.high_value_threshold_paise:
            self.journal_engine.high_value_threshold_paise = request.high_value_threshold_paise
        if request.approval_threshold_paise:
            self.pattern_engine.approval_threshold_paise = request.approval_threshold_paise

        generated_alerts: list[ContinuousAlert] = []

        # 1. Journal Risk Engine
        for entry in entries:
            alert = self.journal_engine.evaluate_journal_entry(request.engagement_id, entry)
            if alert:
                generated_alerts.append(alert)

        # 2. Duplicate Detection
        dup_alerts = self.pattern_engine.detect_duplicate_transactions(request.engagement_id, entries)
        generated_alerts.extend(dup_alerts)

        # 3. Split Transaction Detection
        split_alerts = self.pattern_engine.detect_split_transactions(request.engagement_id, entries)
        generated_alerts.extend(split_alerts)

        # Save alerts with deduplication & fatigue control
        saved_alerts = self.audit_repo.save_alerts(generated_alerts)

        # Count severity
        crit = sum(1 for a in saved_alerts if a.severity == AlertSeverityEnum.CRITICAL)
        high = sum(1 for a in saved_alerts if a.severity == AlertSeverityEnum.HIGH)
        med = sum(1 for a in saved_alerts if a.severity == AlertSeverityEnum.MEDIUM)
        low = sum(1 for a in saved_alerts if a.severity == AlertSeverityEnum.LOW)
        suppressed = len(generated_alerts) - len(saved_alerts)

        dtos = [
            ContinuousAlertDto(
                alert_id=a.alert_id,
                engagement_id=a.engagement_id,
                alert_type=a.alert_type.value,
                severity=a.severity.value,
                title=a.title,
                description=a.description,
                source=a.source,
                risk_score=a.risk_score,
                risk_factors=[
                    RiskFactorContributionDto(
                        factor_name=f.factor_name,
                        score_contribution=f.score_contribution,
                        description=f.description,
                    )
                    for f in a.risk_factors
                ],
                affected_data=a.affected_data,
                status=a.status.value,
                assigned_user=a.assigned_user,
                dedup_hash=a.dedup_hash,
                suppressed=a.suppressed,
                detected_at=a.detected_at.isoformat(),
            )
            for a in saved_alerts
        ]

        return ContinuousMonitoringSummaryDto(
            engagement_id=request.engagement_id,
            transactions_monitored=len(entries),
            alerts_generated=len(saved_alerts),
            critical_alerts=crit,
            high_alerts=high,
            medium_alerts=med,
            low_alerts=low,
            suppressed_alerts=suppressed,
            open_investigations=0,
            confirmed_exceptions=0,
            alerts=dtos,
        )

    def run_continuous_reconciliation(
        self,
        engagement_id: str,
        tb_lines: list[dict[str, Any]],
        subledgers: Optional[dict[str, tuple[int, int]]] = None,
    ) -> list[ContinuousReconciliationRecordModel]:
        records: list[ContinuousReconciliationRecordModel] = []
        now = datetime.now(timezone.utc).isoformat()

        # 1. TB Balance check
        tb_res = self.recon_engine.reconcile_trial_balance(tb_lines)
        rec_tb = ContinuousReconciliationRecordModel(
            id=f"REC-TB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            engagement_id=engagement_id,
            reconciliation_type=tb_res.reconciliation_type,
            expected_paise=tb_res.expected_paise,
            actual_paise=tb_res.actual_paise,
            difference_paise=tb_res.difference_paise,
            threshold_paise=tb_res.threshold_paise,
            status=tb_res.status,
            details=tb_res.details,
            evaluated_at=now,
        )
        self.audit_repo.session.add(rec_tb)
        records.append(rec_tb)

        # 2. Subledger checks if provided
        if subledgers:
            for name, (gl_bal, sub_bal) in subledgers.items():
                sub_res = self.recon_engine.reconcile_subledger_to_gl(name, gl_bal, sub_bal)
                rec_sub = ContinuousReconciliationRecordModel(
                    id=f"REC-{name.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    engagement_id=engagement_id,
                    reconciliation_type=sub_res.reconciliation_type,
                    expected_paise=sub_res.expected_paise,
                    actual_paise=sub_res.actual_paise,
                    difference_paise=sub_res.difference_paise,
                    threshold_paise=sub_res.threshold_paise,
                    status=sub_res.status,
                    details=sub_res.details,
                    evaluated_at=now,
                )
                self.audit_repo.session.add(rec_sub)
                records.append(rec_sub)

        self.audit_repo.session.flush()
        return records

    def get_dashboard_summary(self, engagement_id: str) -> ContinuousAuditDashboardDto:
        session = self.audit_repo.session

        alerts = self.audit_repo.get_alerts(engagement_id, include_suppressed=False)
        total_alerts = len(alerts)
        high_risk = sum(1 for a in alerts if a.severity in (AlertSeverityEnum.CRITICAL, AlertSeverityEnum.HIGH))
        control_breaks = sum(1 for a in alerts if a.alert_type.value == "CONTROL_VIOLATION")
        period_end = sum(1 for a in alerts if "Period-End" in a.title or "Post-Closing" in a.title)
        tax_anomalies = sum(1 for a in alerts if a.alert_type.value == "TAX_ANOMALY")

        dq_stmt = select(DataQualityIssueModel).where(DataQualityIssueModel.engagement_id == engagement_id)
        dq_count = len(session.execute(dq_stmt).scalars().all())

        inv_stmt = select(AlertInvestigationModel).where(AlertInvestigationModel.engagement_id == engagement_id)
        invs = session.execute(inv_stmt).scalars().all()
        open_invs = sum(1 for i in invs if i.status in ("INVESTIGATING", "ASSIGNED"))
        confirmed = sum(1 for i in invs if i.outcome == "Valid Finding")

        return ContinuousAuditDashboardDto(
            engagement_id=engagement_id,
            transactions_monitored=total_alerts * 10,
            alerts_generated=total_alerts,
            high_risk_signals=high_risk,
            open_investigations=open_invs,
            confirmed_exceptions=confirmed,
            potential_misstatements=0,
            control_violations=control_breaks,
            tax_anomalies=tax_anomalies,
            period_end_anomalies=period_end,
            data_quality_issues_count=dq_count,
            materiality_exposure={},
        )
