"""Tests for Unified Findings Model, Source Attribution, and Legal Status Lifecycle."""

import pytest

from finauditpro.application.audit_planning_dtos import (
    CreateFindingDTO,
    UpdateFindingStatusDTO,
)
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.audit_matrix_entities import (
    FindingSourceEnum,
    FindingStatusEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.exceptions import InvalidStateTransitionError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_file = tmp_path / "test_audit_m4.db"
    manager = DatabaseManager(str(db_file))
    manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())
    return manager


@pytest.fixture
def setup_services(db_manager: DatabaseManager):
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    planning_svc = AuditPlanningService(db_manager)

    firm = firm_svc.create_firm(
        CreateFirmDTO(name="Test CA Firm", firm_registration_number="FRN-999999")
    )
    client = client_svc.create_client(
        CreateClientDTO(firm_id=firm.id, name="Test Enterprise Ltd", gstin="27AABCU9603R1ZN")
    )
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2025-26",
            lead_auditor="Lead Auditor",
        )
    )

    return eng, planning_svc


def test_unified_findings_creation_and_sources(setup_services) -> None:
    """Verify single Finding model handles manual, deterministic analytics, and AI sources."""
    eng, planning_svc = setup_services

    # 1. Manual Finding
    f_manual = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            title="Manual Cut-Off Discrepancy",
            description="Tested 5 invoices post year-end.",
            severity=RiskSeverityEnum.HIGH,
            amount_paise=15000000,
            source=FindingSourceEnum.MANUAL,
            is_ai_generated=False,
        )
    )
    assert f_manual.source == FindingSourceEnum.MANUAL
    assert f_manual.is_ai_generated is False
    assert f_manual.status == FindingStatusEnum.OPEN

    # 2. Deterministic Analytic Finding (M3 Accept Path)
    f_analytic = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            title="Duplicate Entry Flagged by Analytics",
            description="Identical debit/credit on same date.",
            severity=RiskSeverityEnum.MEDIUM,
            amount_paise=5000000,
            source=FindingSourceEnum.DETERMINISTIC_ANALYTIC,
            is_ai_generated=False,
        )
    )
    assert f_analytic.source == FindingSourceEnum.DETERMINISTIC_ANALYTIC
    assert f_analytic.is_ai_generated is False

    # 3. AI Finding
    f_ai = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            title="AI Inconsistency Warning",
            description="LLM detected clause mismatch.",
            severity=RiskSeverityEnum.LOW,
            source=FindingSourceEnum.AI,
            is_ai_generated=True,
        )
    )
    assert f_ai.source == FindingSourceEnum.AI
    assert f_ai.is_ai_generated is True


def test_finding_status_lifecycle_transitions(setup_services) -> None:
    """Verify legal state transitions and rejection of illegal transitions."""
    eng, planning_svc = setup_services

    finding = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            title="Test Finding Lifecycle",
            description="Testing state machine.",
        )
    )
    assert finding.status == FindingStatusEnum.OPEN

    # Legal: OPEN -> UNDER_REVIEW
    updated = planning_svc.update_finding_status(
        UpdateFindingStatusDTO(
            finding_id=finding.id,
            new_status=FindingStatusEnum.UNDER_REVIEW,
            reviewer="Senior Partner",
        )
    )
    assert updated.status == FindingStatusEnum.UNDER_REVIEW
    assert updated.reviewer == "Senior Partner"

    # Legal: UNDER_REVIEW -> ACCEPTED
    updated2 = planning_svc.update_finding_status(
        UpdateFindingStatusDTO(finding_id=finding.id, new_status=FindingStatusEnum.ACCEPTED)
    )
    assert updated2.status == FindingStatusEnum.ACCEPTED

    # Legal: ACCEPTED -> CARRIED_FORWARD
    updated3 = planning_svc.update_finding_status(
        UpdateFindingStatusDTO(finding_id=finding.id, new_status=FindingStatusEnum.CARRIED_FORWARD)
    )
    assert updated3.status == FindingStatusEnum.CARRIED_FORWARD


def test_illegal_finding_status_transition_fails(setup_services) -> None:
    """Verify that illegal status transition (e.g. OPEN -> RESOLVED) raises InvalidStateTransitionError."""
    eng, planning_svc = setup_services

    finding = planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            title="Test Illegal Transition",
            description="Testing fail-closed state machine.",
        )
    )
    assert finding.status == FindingStatusEnum.OPEN

    with pytest.raises(InvalidStateTransitionError) as exc_info:
        planning_svc.update_finding_status(
            UpdateFindingStatusDTO(finding_id=finding.id, new_status=FindingStatusEnum.RESOLVED)
        )
    assert "Open" in str(exc_info.value)
    assert "Resolved" in str(exc_info.value)
