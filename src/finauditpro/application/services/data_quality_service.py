"""Service for running data quality validations and managing detected data issues."""

from datetime import UTC, datetime
from typing import Any

from finauditpro.application.continuous_audit_dtos import (
    DataQualityIssueDto,
    DataQualityRunRequest,
    DataQualityRunResultDto,
)
from finauditpro.domain.continuous_audit_entities import (
    AlertSeverityEnum,
    AlertTypeEnum,
    ContinuousAlert,
    DataQualitySeverityEnum,
    RiskFactorContribution,
)
from finauditpro.domain.data_quality_engine import DataQualityEngine
from finauditpro.infrastructure.persistence.continuous_audit_models import DataQualityIssueModel
from finauditpro.infrastructure.persistence.repositories.continuous_audit_repository import (
    ContinuousAuditRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import (
    FinancialDataRepository,
)


class DataQualityService:
    """Orchestrates continuous data quality verification across financial records."""

    def __init__(
        self,
        audit_repo: ContinuousAuditRepository,
        financial_repo: FinancialDataRepository | None = None,
        engine: DataQualityEngine | None = None,
    ):
        self.audit_repo = audit_repo
        self.financial_repo = financial_repo
        self.engine = engine or DataQualityEngine()

    def run_data_quality_checks(
        self,
        request: DataQualityRunRequest,
        entries_override: list[dict[str, Any]] | None = None,
    ) -> DataQualityRunResultDto:
        entries: list[dict[str, Any]] = []
        known_accounts: set[str] = set()

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
            # Fetch chart of accounts if available
            tb_lines = self.financial_repo.get_trial_balance_lines(request.dataset_id)
            known_accounts = {t.account_code for t in tb_lines if t.account_code}

        issues = self.engine.evaluate_ledger_entries(
            engagement_id=request.engagement_id,
            dataset_id=request.dataset_id or "DATASET-001",
            entries=entries,
            known_account_codes=known_accounts if known_accounts else None,
            period_start=request.period_start,
            period_end=request.period_end,
            as_of_date=request.as_of_date,
        )

        # Save issues to database
        self.audit_repo.save_data_quality_issues(issues)

        # Promote critical/high data quality issues to continuous alerts
        alerts_to_create: list[ContinuousAlert] = []
        for issue in issues:
            if issue.severity in (DataQualitySeverityEnum.CRITICAL, DataQualitySeverityEnum.HIGH):
                alerts_to_create.append(
                    ContinuousAlert(
                        alert_id=f"ALT-DQ-{issue.issue_id[-8:]}",
                        engagement_id=issue.engagement_id,
                        alert_type=AlertTypeEnum.UNUSUAL_TRANSACTION,
                        severity=AlertSeverityEnum.CRITICAL if issue.severity == DataQualitySeverityEnum.CRITICAL else AlertSeverityEnum.HIGH,
                        title=f"Data Quality Exception: {issue.issue_type.value}",
                        description=issue.description,
                        source="Continuous Data Quality Guard",
                        detected_at=issue.detected_at,
                        affected_data={"issue_id": issue.issue_id, "affected_records": issue.affected_records},
                        risk_score=75.0 if issue.severity == DataQualitySeverityEnum.CRITICAL else 55.0,
                        risk_factors=[
                            RiskFactorContribution(
                                factor_name=issue.issue_type.value,
                                score_contribution=75.0 if issue.severity == DataQualitySeverityEnum.CRITICAL else 55.0,
                                description=issue.description,
                            )
                        ],
                        dedup_hash=f"DQ-{issue.issue_id}",
                    )
                )
        if alerts_to_create:
            self.audit_repo.save_alerts(alerts_to_create)

        crit = sum(1 for i in issues if i.severity == DataQualitySeverityEnum.CRITICAL)
        high = sum(1 for i in issues if i.severity == DataQualitySeverityEnum.HIGH)
        med = sum(1 for i in issues if i.severity == DataQualitySeverityEnum.MEDIUM)
        low = sum(1 for i in issues if i.severity == DataQualitySeverityEnum.LOW)

        dtos = [
            DataQualityIssueDto(
                issue_id=i.issue_id,
                engagement_id=i.engagement_id,
                dataset_id=i.dataset_id,
                issue_type=i.issue_type.value,
                severity=i.severity.value,
                source=i.source,
                description=i.description,
                affected_records=i.affected_records,
                detected_at=i.detected_at.isoformat(),
                resolution=i.resolution,
                resolved_by=i.resolved_by,
                resolved_at=i.resolved_at.isoformat() if i.resolved_at else None,
            )
            for i in issues
        ]

        return DataQualityRunResultDto(
            engagement_id=request.engagement_id,
            total_issues=len(issues),
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            issues=dtos,
        )

    def resolve_data_quality_issue(
        self, issue_id: str, resolution: str, resolved_by: str
    ) -> bool:
        session = self.audit_repo.session
        model = session.get(DataQualityIssueModel, issue_id)
        if not model:
            return False
        model.resolution = resolution
        model.resolved_by = resolved_by
        model.resolved_at = datetime.now(UTC).isoformat()
        session.flush()
        return True
