"""Unit tests for SA 320 Materiality calculations and service."""

import pytest

from finauditpro.application.audit_matrix_dtos import CalculateMaterialityDTO
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.domain.audit_matrix_entities import BenchmarkTypeEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def setup_services(tmp_path):
    db_path = tmp_path / "test_mat_svc.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Mat Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Mat Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    mat_svc = MaterialityService(manager)
    return manager, eng, mat_svc


def test_sa320_materiality_calculations(setup_services) -> None:
    _manager, eng, mat_svc = setup_services

    dto = CalculateMaterialityDTO(
        engagement_id=eng.id,
        benchmark_type=BenchmarkTypeEnum.REVENUE,
        benchmark_amount=50000000.0,  # INR 5 Crore Revenue
        overall_percentage=1.0,       # 1%
        performance_percentage=75.0,  # 75% of overall
        trivial_percentage=5.0,       # 5% of overall
    )

    mat = mat_svc.calculate_and_save_materiality(dto)
    assert mat.overall_materiality == 500000.0        # INR 5 Lakh
    assert mat.performance_materiality == 375000.0   # INR 3.75 Lakh
    assert mat.clearly_trivial_threshold == 25000.0   # INR 25 Thousand
    assert mat.version == 1

    # Retrieve latest
    latest = mat_svc.get_latest_materiality(eng.id)
    assert latest is not None
    assert latest.overall_materiality == 500000.0
