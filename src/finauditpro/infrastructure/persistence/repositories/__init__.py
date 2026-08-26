"""Package re-exporting all domain repositories for persistence operations."""

from finauditpro.infrastructure.persistence.repositories.archival_repository import (
    ArchivalRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_event_repository import (
    AuditEventRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.client_repository import ClientRepository
from finauditpro.infrastructure.persistence.repositories.document_repository import (
    DocumentRepository,
)
from finauditpro.infrastructure.persistence.repositories.engagement_repository import (
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.evidence_repository import (
    EvidenceRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import (
    FinancialDataRepository,
)
from finauditpro.infrastructure.persistence.repositories.firm_repository import FirmRepository
from finauditpro.infrastructure.persistence.repositories.report_repository import ReportRepository
from finauditpro.infrastructure.persistence.repositories.roll_forward_repository import (
    RollForwardRepository,
)
from finauditpro.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)

__all__ = [
    "ArchivalRepository",
    "AuditEventRepository",
    "AuditMatrixRepository",
    "ClientRepository",
    "DocumentRepository",
    "EngagementRepository",
    "EvidenceRepository",
    "FinancialDataRepository",
    "FirmRepository",
    "ReportRepository",
    "RollForwardRepository",
    "UserRepository",
    "WorkingPaperRepository",
]
