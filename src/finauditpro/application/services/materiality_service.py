"""SA 320 Materiality Calculation Engine and Service."""

from finauditpro.application.audit_matrix_dtos import CalculateMaterialityDTO
from finauditpro.domain.audit_matrix_entities import MaterialityAssessment
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    EngagementRepository,
)


class MaterialityService:
    """Service executing deterministic SA 320 materiality calculations with version tracking."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def calculate_and_save_materiality(self, dto: CalculateMaterialityDTO) -> MaterialityAssessment:
        """Compute SA 320 materiality thresholds deterministically and persist assessment."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            matrix_repo = AuditMatrixRepository(session)
            existing = matrix_repo.get_latest_materiality(dto.engagement_id)
            next_version = (existing.version + 1) if existing else 1

        bm_paise = int(round(dto.benchmark_amount * 100))
        om_paise = int(round(bm_paise * (dto.overall_percentage / 100.0)))
        pm_paise = int(round(om_paise * (dto.performance_percentage / 100.0)))
        ctt_paise = int(round(om_paise * (dto.trivial_percentage / 100.0)))

        mat_assessment = MaterialityAssessment(
            engagement_id=dto.engagement_id,
            benchmark_type=dto.benchmark_type,
            benchmark_amount_paise=bm_paise,
            overall_percentage=dto.overall_percentage,
            overall_materiality_paise=om_paise,
            performance_percentage=dto.performance_percentage,
            performance_materiality_paise=pm_paise,
            trivial_percentage=dto.trivial_percentage,
            clearly_trivial_threshold_paise=ctt_paise,
            version=next_version,
            created_by=dto.created_by,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            saved_mat = repo.add_materiality_assessment(mat_assessment)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.created_by,
                    action="SA 320 Materiality Calculated",
                    details=f"Calculated SA 320 Materiality v{next_version}: Overall = {mat_assessment.overall_materiality.formatted}, Performance = {mat_assessment.performance_materiality.formatted}, Clearly Trivial = {mat_assessment.clearly_trivial_threshold.formatted} (Benchmark: {dto.benchmark_type.value} = {mat_assessment.benchmark_amount.formatted})",
                )
            )

        return saved_mat

    def get_latest_materiality(self, engagement_id: str) -> MaterialityAssessment | None:
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.get_latest_materiality(engagement_id)

    def list_materiality_history(self, engagement_id: str) -> list[MaterialityAssessment]:
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.list_materiality_history(engagement_id)
