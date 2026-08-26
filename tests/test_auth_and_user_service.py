"""Unit and integration tests for authentication, user management, and session-bound workflows."""

import pytest

from finauditpro.application.audit_matrix_dtos import CalculateMaterialityDTO
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.auth_service import AuthService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.audit_matrix_entities import BenchmarkTypeEnum
from finauditpro.domain.entities import RoleEnum
from finauditpro.domain.exceptions import ValidationError
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
    hash_password,
    verify_password,
)


@pytest.fixture
def db_env(tmp_path):
    db_file = tmp_path / "test_auth.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    return db_manager


def test_password_hashing_and_verification():
    pwd = "AuditSecretPassword@2026"
    h, salt = hash_password(pwd)
    assert h is not None and len(h) == 64
    assert salt is not None and len(salt) == 32
    assert verify_password(pwd, h, salt) is True
    assert verify_password("WrongPassword", h, salt) is False


def test_user_repository_and_default_admin(db_env):
    with db_env.session_scope() as session:
        repo = UserRepository(session)
        admin = repo.seed_default_admin_if_empty()
        assert admin is not None
        assert admin.username == "admin@finauditpro.com"
        assert admin.role == RoleEnum.ADMINISTRATOR

        # Second seed should be no-op
        assert repo.seed_default_admin_if_empty() is None

        # Lookup
        found = repo.get_by_username("ADMIN@finauditpro.com")
        assert found is not None
        assert found.id == admin.id


def test_auth_service_flow(db_env):
    auth_svc = AuthService(db_env)

    # 1. Valid login with seeded admin
    session = auth_svc.authenticate("admin@finauditpro.com", "Admin@123")
    assert isinstance(session, UserSession)
    assert session.username == "admin@finauditpro.com"
    assert session.role == RoleEnum.ADMINISTRATOR

    # 2. Invalid password
    with pytest.raises(ValidationError, match="Invalid username or password"):
        auth_svc.authenticate("admin@finauditpro.com", "WrongPass")

    # 3. Non-existent user
    with pytest.raises(ValidationError, match="Invalid username or password"):
        auth_svc.authenticate("nonexistent@firm.com", "Pass@123")

    # 4. Create new auditor user
    auditor = auth_svc.create_user(
        username="senior_auditor@firm.com",
        password="SeniorPass@123",
        role=RoleEnum.SENIOR,
    )
    assert auditor.username == "senior_auditor@firm.com"
    assert auditor.role == RoleEnum.SENIOR

    # 5. Authenticate new user
    auditor_session = auth_svc.authenticate("senior_auditor@firm.com", "SeniorPass@123")
    assert auditor_session.role == RoleEnum.SENIOR


def test_segregation_of_duties_with_authenticated_preparer(db_env):
    firm_svc = FirmService(db_env)
    client_svc = ClientService(db_env)
    eng_svc = EngagementService(db_env)
    wp_svc = WorkingPaperService(db_env)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Test Audit Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Test Corp"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    # Working paper prepared by senior auditor
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-001",
            title="Revenue Audit",
            area="Revenue",
            preparer_id="senior_auditor@firm.com",
        )
    )
    assert wp.preparer_id == "senior_auditor@firm.com"

    # Preparer tries to perform final partner sign-off on their own workpaper -> must fail SoD
    with pytest.raises(ValidationError, match="Segregation of Duties Violation"):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="senior_auditor@firm.com",
                user_role="Partner",
                note="Attempting self signoff",
            )
        )

    # Different partner signs off -> succeeds
    signoff = wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="partner_lead@firm.com",
            user_role="Partner",
            note="Reviewed and approved",
        )
    )
    assert signoff is not None
    assert wp_svc.get_working_paper(wp.id).is_locked is True


def test_materiality_service_delegates_to_engine(db_env):
    firm_svc = FirmService(db_env)
    client_svc = ClientService(db_env)
    eng_svc = EngagementService(db_env)
    mat_svc = MaterialityService(db_env)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Mat Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Mat Corp"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    mat = mat_svc.calculate_and_save_materiality(
        CalculateMaterialityDTO(
            engagement_id=eng.id,
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount=50000000.0,  # 5 Crore INR = 5,00,000,000 paise
            overall_percentage=1.0,  # 50,00,000 paise
            performance_percentage=75.0,  # 37,50,000 paise
            trivial_percentage=5.0,  # 2,50,000 paise
            created_by="Lead Partner",
        )
    )
    assert mat.overall_materiality_paise == 50000000
    assert mat.performance_materiality_paise == 37500000
    assert mat.clearly_trivial_threshold_paise == 2500000
    assert mat.version == 1


def test_forced_password_reset_flow(db_env):
    auth_svc = AuthService(db_env)

    # 1. Initial admin seeded with must_change_password=True
    session = auth_svc.authenticate("admin@finauditpro.com", "Admin@123")
    assert session.must_change_password is True

    # 2. Reject weak passwords
    with pytest.raises(ValidationError, match="at least 8 characters"):
        auth_svc.force_change_password(session.user_id, "short")

    with pytest.raises(ValidationError, match="cannot be the default"):
        auth_svc.force_change_password(session.user_id, "Admin@123")

    with pytest.raises(ValidationError, match="at least one number"):
        auth_svc.force_change_password(session.user_id, "OnlyLettersPassword")

    # 3. Successful password update
    new_pwd = "NewMasterPassword#2026"
    updated_session = auth_svc.force_change_password(session.user_id, new_pwd)
    assert updated_session.must_change_password is False

    # 4. Old default password Admin@123 no longer works
    with pytest.raises(ValidationError, match="Invalid username or password"):
        auth_svc.authenticate("admin@finauditpro.com", "Admin@123")

    # 5. New password works and must_change_password is False
    subsequent_session = auth_svc.authenticate("admin@finauditpro.com", new_pwd)
    assert subsequent_session.must_change_password is False
