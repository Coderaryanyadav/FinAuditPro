"""Tests for Multi-Tenant Engagement Isolation in Milestone 4."""

import pytest

from finauditpro.application.audit_planning_dtos import (
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
    SetMaterialityDTO,
)
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.audit_matrix_entities import BenchmarkTypeEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_isolation_env(tmp_path):
    db_file = tmp_path / "test_isolation_m4.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    planning_svc = AuditPlanningService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Isolation Firm", firm_registration_number="FRN-777777"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha", gstin="27AAAAA9603R1ZN"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta", gstin="27BBBBB9603R1ZN"))

    eng_a = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26", lead_auditor="Auditor A"))
    eng_b = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26", lead_auditor="Auditor B"))

    return eng_a, eng_b, planning_svc


def test_engagement_isolation_planning_entities(setup_isolation_env) -> None:
    """Verify risks, procedures, materiality, and findings of Engagement A never leak to Engagement B."""
    eng_a, eng_b, planning_svc = setup_isolation_env

    # 1. Create entities under Engagement A
    planning_svc.set_materiality(
        SetMaterialityDTO(
            engagement_id=eng_a.id,
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount_paise=100000000,
        )
    )

    planning_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng_a.id,
            risk_code="RSK-ALPHA-01",
            title="Alpha Risk",
            category="Revenue",
            description="Alpha description.",
        )
    )

    planning_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng_a.id,
            procedure_code="PROC-ALPHA-01",
            objective="Alpha objective.",
        )
    )

    planning_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng_a.id,
            title="Alpha Finding",
            description="Alpha finding detail.",
        )
    )

    # 2. Verify Engagement B returns ZERO entities of Engagement A
    assert planning_svc.get_latest_materiality(eng_b.id) is None
    assert len(planning_svc.list_materiality_history(eng_b.id)) == 0
    assert len(planning_svc.list_risks(eng_b.id)) == 0
    assert len(planning_svc.list_procedures(eng_b.id)) == 0
    assert len(planning_svc.list_findings(eng_b.id)) == 0

    # 3. Verify Engagement A returns exactly 1 of each entity
    assert planning_svc.get_latest_materiality(eng_a.id) is not None
    assert len(planning_svc.list_risks(eng_a.id)) == 1
    assert len(planning_svc.list_procedures(eng_a.id)) == 1
    assert len(planning_svc.list_findings(eng_a.id)) == 1
