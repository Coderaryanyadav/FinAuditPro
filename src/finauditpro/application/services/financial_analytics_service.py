import json
from typing import cast

from finauditpro.application.financial_dtos import RunAnalyticsDTO
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.domain.financial_entities import (
    AnalyticsResult,
    AnalyticsTypeEnum,
    FlaggedAnomaly,
)
from finauditpro.infrastructure.analytics.analytics_engine import (
    DeterministicAnalyticsEngine,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    FinancialDataRepository,
)


class FinancialAnalyticsService:
    """Service executing deterministic analytics routines and persisting reproducible results."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def run_analysis(self, dto: RunAnalyticsDTO) -> AnalyticsResult:
        """Execute specified deterministic analysis on dataset and record findings."""
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            dataset = repo.get_dataset(dto.dataset_id)
            if not dataset:
                raise EntityNotFoundError("Financial Dataset", dto.dataset_id)

            records = repo.get_dataset_records(dto.dataset_id)

        # Prepare dict representation for engine
        record_dicts = [
            {
                "row_index": r.row_index,
                "transaction_id": r.transaction_id,
                "date": r.date,
                "account_name": r.account_name,
                "amount": r.amount,
                "invoice_number": r.invoice_number,
            }
            for r in records
        ]

        # Dispatch to deterministic engine algorithm
        if dto.analysis_type == AnalyticsTypeEnum.DUPLICATE_DETECTION:
            output = DeterministicAnalyticsEngine.find_duplicates(record_dicts)
        elif dto.analysis_type == AnalyticsTypeEnum.HIGH_VALUE_ANOMALY:
            threshold = dto.threshold if dto.threshold is not None else 500000.0
            output = DeterministicAnalyticsEngine.find_large_amounts(
                record_dicts, threshold=threshold
            )
        elif dto.analysis_type == AnalyticsTypeEnum.ROUND_NUMBER_CHECK:
            output = DeterministicAnalyticsEngine.find_round_numbers(record_dicts)
        elif dto.analysis_type == AnalyticsTypeEnum.WEEKEND_POSTING_CHECK:
            output = DeterministicAnalyticsEngine.find_weekend_transactions(record_dicts)
        elif dto.analysis_type == AnalyticsTypeEnum.SEQUENCE_GAP_CHECK:
            output = DeterministicAnalyticsEngine.find_sequence_gaps(record_dicts)
        else:
            output = DeterministicAnalyticsEngine.find_duplicates(record_dicts)

        result_entity = AnalyticsResult(
            engagement_id=dto.engagement_id,
            dataset_id=dto.dataset_id,
            analysis_type=dto.analysis_type,
            parameters_json=json.dumps(output.parameters),
            anomaly_count=output.anomaly_count,
            summary=output.summary,
            reproducible_explanation=output.reproducible_explanation,
        )

        anomalies = [
            FlaggedAnomaly(
                analytics_result_id=result_entity.id,
                dataset_id=dto.dataset_id,
                row_index=m.row_index,
                transaction_id=m.transaction_id,
                date=m.date,
                amount=m.amount,
                account_name=m.account_name,
                rationale=m.rationale,
                severity=m.severity,
            )
            for m in output.anomalies
        ]

        with self.db_manager.session_scope() as session:
            fin_repo = FinancialDataRepository(session)
            saved_result = fin_repo.add_analytics_result(result_entity, anomalies)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor="System",
                    action=f"Analytics Run: {dto.analysis_type.value}",
                    details=f"Ran {dto.analysis_type.value} on dataset '{dto.dataset_id[:8]}...'. Flagged {output.anomaly_count} anomalies requiring review.",
                )
            )

        return cast(AnalyticsResult, saved_result)

    def list_analytics_results_for_engagement(self, engagement_id: str) -> list[AnalyticsResult]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            return cast(
                list[AnalyticsResult], repo.list_analytics_results_for_engagement(engagement_id)
            )

    def list_flagged_anomalies_for_engagement(self, engagement_id: str) -> list[FlaggedAnomaly]:
        with self.db_manager.session_scope() as session:
            repo = FinancialDataRepository(session)
            return repo.list_flagged_anomalies_for_engagement(engagement_id)
