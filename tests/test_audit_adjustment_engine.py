"""Tests for Audit Adjusting Journal Entries (AJE) engine, double-entry invariants, and maker-checker security."""

import pytest

from finauditpro.application.audit_adjustment_dtos import (
    ApplyAJEDTO,
    CreateAJEDTO,
    CreateAJELineDTO,
    ReverseAJEDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.domain.audit_adjustment_entities import AJEStatusEnum, AJETypeEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    RoleEnum,
    User,
)
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture(autouse=True)
def clean_security_context():
    SecurityContext.clear()
    yield
    SecurityContext.clear()


@pytest.fixture
def db_manager(tmp_path):
    db_path = tmp_path / "test_aje.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_environment(db_manager):
    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = firm_repo.add(Firm(id="firm-1", name="CA Audit Firm"))

        user_repo = UserRepository(session)
        user_repo.add(
            User(
                id="user-associate",
                username="assoc1",
                password_hash="h",
                salt="s",
                role="Associate",
            )
        )
        user_repo.add(
            User(id="user-senior", username="senior1", password_hash="h", salt="s", role="Senior")
        )
        user_repo.add(
            User(
                id="user-partner", username="partner1", password_hash="h", salt="s", role="Partner"
            )
        )

        client_repo = ClientRepository(session)
        client = client_repo.add(
            Client(id="client-1", firm_id=firm.id, name="ABC Manufacturing Pvt Ltd")
        )

        eng_repo = EngagementRepository(session)
        eng1 = eng_repo.add(
            Engagement(
                id="eng-1",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        eng2 = eng_repo.add(
            Engagement(
                id="eng-2",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2024-25",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        return eng1, eng2


def test_valid_double_entry_aje_creation(db_manager, seed_environment):
    eng1, _ = seed_environment
    service = AuditAdjustmentService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-associate", username="assoc1", role=RoleEnum.ASSOCIATE)
    )

    # Dr Audit Fee Expense ₹50,000, Cr Audit Fee Payable ₹50,000
    dto = CreateAJEDTO(
        engagement_id=eng1.id,
        aje_number="AJE-001",
        entry_date="2026-03-31",
        title="Unrecorded Audit Fee Provision",
        narration="Provision for statutory audit fees for FY 2025-26",
        reason="Audit fee unaccrued in client books",
        working_paper_ref="WP-C3",
        aje_type=AJETypeEnum.MANAGEMENT_ACCEPTED,
        lines=[
            CreateAJELineDTO(
                account_code="4001",
                account_name="Audit Fees Expense",
                debit_paise=5000000,
                credit_paise=0,
            ),
            CreateAJELineDTO(
                account_code="2005",
                account_name="Audit Fees Payable",
                debit_paise=0,
                credit_paise=5000000,
            ),
        ],
    )
    created = service.create_adjustment(dto)
    assert created.id is not None
    assert created.status == AJEStatusEnum.DRAFT
    assert created.total_debit_paise == 5000000
    assert created.total_credit_paise == 5000000
    assert len(created.lines) == 2


def test_invalid_unbalanced_aje_rejection(db_manager, seed_environment):
    eng1, _ = seed_environment
    service = AuditAdjustmentService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-associate", username="assoc1", role=RoleEnum.ASSOCIATE)
    )

    # Unbalanced AJE: Dr ₹50,000 vs Cr ₹45,000
    dto = CreateAJEDTO(
        engagement_id=eng1.id,
        aje_number="AJE-BAD",
        entry_date="2026-03-31",
        title="Unbalanced Entry",
        narration="Test bad entry",
        reason="Testing double-entry validator",
        lines=[
            CreateAJELineDTO(
                account_code="4001", account_name="Audit Fees", debit_paise=5000000, credit_paise=0
            ),
            CreateAJELineDTO(
                account_code="2005", account_name="Payables", debit_paise=0, credit_paise=4500000
            ),
        ],
    )
    with pytest.raises(ValidationError, match="Double-Entry Violation"):
        service.create_adjustment(dto)


def test_maker_checker_segregation_of_duties(db_manager, seed_environment):
    eng1, _ = seed_environment
    service = AuditAdjustmentService(db_manager)

    # 1. Associate prepares AJE
    SecurityContext.set_current_session(
        UserSession(user_id="user-associate", username="assoc1", role=RoleEnum.ASSOCIATE)
    )
    aje = service.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-002",
            entry_date="2026-03-31",
            title="Depreciation Understatement Adjustment",
            narration="Adjustment for Schedule II useful life correction",
            reason="Useful life of Plant adjusted from 15 to 10 years",
            lines=[
                CreateAJELineDTO(
                    account_code="5001",
                    account_name="Depreciation Expense",
                    debit_paise=12000000,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="1050",
                    account_name="Accumulated Depreciation",
                    debit_paise=0,
                    credit_paise=12000000,
                ),
            ],
        )
    )
    service.submit_adjustment(SubmitAJEDTO(engagement_id=eng1.id, entry_id=aje.id))

    # 2. Associate attempts to approve their own AJE -> MUST BE BLOCKED
    SecurityContext.set_current_session(
        UserSession(user_id="user-associate", username="assoc1", role=RoleEnum.ASSOCIATE)
    )
    with pytest.raises(PermissionDeniedError, match="Maker-Checker Violation"):
        service.review_adjustment(
            ReviewAJEDTO(engagement_id=eng1.id, entry_id=aje.id, decision="APPROVE")
        )

    # 3. Senior Auditor reviews and approves -> SUCCESS
    SecurityContext.set_current_session(
        UserSession(user_id="user-senior", username="senior1", role=RoleEnum.SENIOR)
    )
    approved = service.review_adjustment(
        ReviewAJEDTO(engagement_id=eng1.id, entry_id=aje.id, decision="APPROVE")
    )
    assert approved.status == AJEStatusEnum.APPROVED
    assert approved.reviewed_by == "user-senior"


def test_aje_reversal_mechanism(db_manager, seed_environment):
    eng1, _ = seed_environment
    service = AuditAdjustmentService(db_manager)

    # Create, Submit, Approve, Apply AJE
    SecurityContext.set_current_session(
        UserSession(user_id="user-associate", username="assoc1", role=RoleEnum.ASSOCIATE)
    )
    aje = service.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-003",
            entry_date="2026-03-31",
            title="Prepaid Insurance Reclassification",
            narration="Reclassify prepaid expense",
            reason="Unexpired insurance policy period",
            lines=[
                CreateAJELineDTO(
                    account_code="1080",
                    account_name="Prepaid Insurance",
                    debit_paise=2500000,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="5020",
                    account_name="Insurance Expense",
                    debit_paise=0,
                    credit_paise=2500000,
                ),
            ],
        )
    )
    service.submit_adjustment(SubmitAJEDTO(engagement_id=eng1.id, entry_id=aje.id))

    SecurityContext.set_current_session(
        UserSession(user_id="user-senior", username="senior1", role=RoleEnum.SENIOR)
    )
    service.review_adjustment(
        ReviewAJEDTO(engagement_id=eng1.id, entry_id=aje.id, decision="APPROVE")
    )
    applied = service.apply_adjustment(ApplyAJEDTO(engagement_id=eng1.id, entry_id=aje.id))
    assert applied.status == AJEStatusEnum.APPLIED

    # Reverse the AJE
    reversal = service.reverse_adjustment(
        ReverseAJEDTO(
            engagement_id=eng1.id,
            entry_id=applied.id,
            reversal_aje_number="REV-AJE-003",
            reason="Management provided policy cancellation endorsement",
        )
    )
    assert reversal.aje_number == "REV-AJE-003"
    assert reversal.status == AJEStatusEnum.APPLIED
    assert reversal.reversal_of_entry_id == applied.id

    # Verify lines are swapped: Dr Insurance Expense, Cr Prepaid Insurance
    assert reversal.lines[0].account_code == "1080" and reversal.lines[0].credit_paise == 2500000
    assert reversal.lines[1].account_code == "5020" and reversal.lines[1].debit_paise == 2500000

    # Verify original entry is marked REVERSED
    all_ajes = {a.id: a for a in service.list_adjustments(eng1.id)}
    assert all_ajes[applied.id].status == AJEStatusEnum.REVERSED


def test_cross_engagement_tenant_isolation(db_manager, seed_environment):
    eng1, eng2 = seed_environment
    service = AuditAdjustmentService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="user-associate", username="assoc1", role=RoleEnum.ASSOCIATE)
    )
    aje1 = service.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng1.id,
            aje_number="AJE-ENG1",
            entry_date="2026-03-31",
            title="Eng 1 Adjustment",
            narration="Eng 1 test",
            reason="Isolation test",
            lines=[
                CreateAJELineDTO(
                    account_code="1001", account_name="Cash", debit_paise=1000, credit_paise=0
                ),
                CreateAJELineDTO(
                    account_code="2001", account_name="Loan", debit_paise=0, credit_paise=1000
                ),
            ],
        )
    )

    # Attempt to access or submit AJE1 from Engagement 2 context -> MUST FAIL
    SecurityContext.set_current_session(
        UserSession(user_id="user-associate", username="assoc1", role=RoleEnum.ASSOCIATE)
    )
    with pytest.raises(EntityNotFoundError):
        service.submit_adjustment(SubmitAJEDTO(engagement_id=eng2.id, entry_id=aje1.id))
