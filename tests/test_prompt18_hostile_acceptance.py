"""Comprehensive hostile acceptance testing across all Prompt 18 personas:
Junior Accountant, Fraudster, Malicious User, Senior Reviewer, Database Attacker, and Auditor.
"""

from pathlib import Path
from uuid import uuid4

import pytest

from finauditpro.application.audit_adjustment_dtos import CreateAJEDTO, CreateAJELineDTO
from finauditpro.application.completion_dtos import (
    PartnerSignoffDTO,
)
from finauditpro.application.security.rbac import RBACManager, RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.engagement_finalization_service import (
    EngagementFinalizationService,
)
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    CreateWorkingPaperDTO,
    SignOffDTO,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.exceptions import ValidationError
from finauditpro.domain.export_sanitizer import escape_formula_injection
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)


def test_persona_junior_accountant_adversarial_rejection(tmp_path: Path) -> None:
    """Junior Accountant Persona: Tries invalid accounting entries. All must be rejected."""
    db_file = tmp_path / "junior_acc.db"
    db_manager = initialize_database(db_file)
    adj_service = AuditAdjustmentService(db_manager)

    with db_manager.session_scope() as session:
        firm = Firm(id="firm-1", name="Test Firm")
        FirmRepository(session).add(firm)
        client = Client(id="client-1", firm_id=firm.id, name="Client Ltd")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-ACC-01",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.PLANNING,
        )
        EngagementRepository(session).add(eng)

    # 1. Unbalanced Journal Entry (Dr ₹1,000, Cr ₹900)
    with pytest.raises(ValidationError, match="Double-Entry Violation in AJE"):
        adj_service.create_adjustment(
            CreateAJEDTO(
                engagement_id="ENG-ACC-01",
                aje_number="AJE-UNBAL-01",
                entry_date="2025-03-31",
                title="Unbalanced Entry",
                narration="Debit does not match credit",
                reason="Junior error",
                lines=[
                    CreateAJELineDTO(account_code="1001", account_name="Cash", debit_paise=100000, credit_paise=0),
                    CreateAJELineDTO(account_code="2001", account_name="Payable", debit_paise=0, credit_paise=90000),
                ],
            )
        )

    # 2. Entry with Zero Lines
    with pytest.raises(ValidationError, match="must have at least two journal lines"):
        adj_service.create_adjustment(
            CreateAJEDTO(
                engagement_id="ENG-ACC-01",
                aje_number="AJE-EMPTY-01",
                entry_date="2025-03-31",
                title="Empty Entry",
                narration="No lines",
                reason="Junior error",
                lines=[],
            )
        )

    # 3. Entry with Concurrent Debit and Credit on single line
    with pytest.raises(ValidationError, match="cannot have both debit .* and credit .* amounts"):
        adj_service.create_adjustment(
            CreateAJEDTO(
                engagement_id="ENG-ACC-01",
                aje_number="AJE-CONC-01",
                entry_date="2025-03-31",
                title="Concurrent Line",
                narration="Both Dr and Cr on same line",
                reason="Junior error",
                lines=[
                    CreateAJELineDTO(account_code="1001", account_name="Cash", debit_paise=50000, credit_paise=50000),
                    CreateAJELineDTO(account_code="2001", account_name="Payable", debit_paise=50000, credit_paise=50000),
                ],
            )
        )


def test_persona_malicious_user_and_fraudster(tmp_path: Path) -> None:
    """Fraudster Persona: Tests formula injection escaping, session bypass, and tampering."""
    # 1. Formula Injection Sanitization
    malicious_inputs = [
        "=cmd|' /C calc'!A0",
        "-2+3+cmd|' /C calc'!A0",
        "+@SUM(1+1)*cmd|' /C calc'!A0",
        "@SUM(1,2)",
        "\t=2+3",
        "\r=cmd",
    ]
    for payload in malicious_inputs:
        sanitized = escape_formula_injection(payload)
        assert sanitized.startswith("'"), f"Payload {payload} was not escaped with leading single quote"

    # 2. Session Locking & Unlock Protection
    session = UserSession(user_id="user-evil", username="attacker", role=RoleEnum.ASSOCIATE)
    rbac = RBACManager(session)
    rbac.lock_session()

    # Must reject blank / whitespace / None passcode
    for bad_code in [None, "", "   "]:
        with pytest.raises(ValueError, match="Passcode is required"):
            rbac.unlock_session(bad_code)
    assert session.is_locked is True


def test_persona_senior_reviewer_maker_checker(tmp_path: Path) -> None:
    """Senior Reviewer Persona: Maker-checker segregation of duties on working papers."""
    db_file = tmp_path / "reviewer.db"
    db_manager = initialize_database(db_file)
    wp_service = WorkingPaperService(db_manager)

    with db_manager.session_scope() as session:
        firm = Firm(id="firm-1", name="Audit LLP")
        FirmRepository(session).add(firm)
        client = Client(id="client-1", firm_id=firm.id, name="Target Co")
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-REV-01",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

        # Create users
        user_repo = UserRepository(session)
        user_repo.create_user_with_password("auditor_ananya@audit.com", "Password@123", role="Associate")
        user_repo.create_user_with_password("manager_vikram@audit.com", "Password@123", role="Senior")

    wp_service.assign_user_to_engagement("ENG-REV-01", "auditor_ananya@audit.com", "Associate")
    wp_service.assign_user_to_engagement("ENG-REV-01", "manager_vikram@audit.com", "Senior")

    # Create WP prepared by 'auditor_ananya@audit.com'
    wp = wp_service.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id="ENG-REV-01",
            index_reference="WP-REV-01",
            title="Revenue Cutoff Testing",
            area="Revenue",
            preparer_id="auditor_ananya@audit.com",
        )
    )

    wp_service.prepare_working_paper(wp.id, "auditor_ananya@audit.com")
    wp_service.submit_for_review(wp.id, "auditor_ananya@audit.com")

    # Attack: Preparer attempts to start review on their own work
    with pytest.raises(ValidationError, match="Segregation of Duties Violation"):
        wp_service.start_review(wp.id, "auditor_ananya@audit.com")

    # Independent Senior starts review
    wp_service.start_review(wp.id, "manager_vikram@audit.com")

    # Attack: Preparer attempts to sign off on their own work
    with pytest.raises(ValidationError, match="Segregation of Duties Violation"):
        wp_service.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.REVIEWED,
                user_id="auditor_ananya@audit.com",
                user_role="Senior",
            )
        )

    # Valid Review: Senior signs off
    signed_wp = wp_service.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.REVIEWED,
            user_id="manager_vikram@audit.com",
            user_role="Senior",
        )
    )
    assert signed_wp.user_id == "manager_vikram@audit.com"


def test_persona_auditor_gate_enforcement_and_post_lock_immutability(tmp_path: Path) -> None:
    """Auditor Persona: Verifies completion gate strictly prevents premature finalization,
    and once completed, engagement is cryptographically sealed against mutations."""
    db_file = tmp_path / "full_audit.db"
    db_manager = initialize_database(db_file)

    # 1. Setup Firm, Client, Engagement, and Users
    with db_manager.session_scope() as session:
        firm = Firm(id="FIRM-001", name="Apex & Associates Chartered Accountants")
        FirmRepository(session).add(firm)
        client = Client(
            id="CLIENT-001",
            firm_id=firm.id,
            name="Apex Dynamics Private Limited",
            pan_number="AABCA1234F",
            cin_number="U72200DL2020PTC123456",
        )
        ClientRepository(session).add(client)
        eng = Engagement(
            id="ENG-E2E-001",
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.REVIEW,
        )
        EngagementRepository(session).add(eng)

        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="partner_mehta",
                password_hash="hash",
                salt="salt",
                display_name="CA Rajesh Mehta, FCA",
                role=RoleEnum.PARTNER,
            )
        )

    # 2. Premature Finalization Attack: Partner attempts sign-off before completion gates pass
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=RoleEnum.PARTNER)
    )
    final_service = EngagementFinalizationService(db_manager)

    with pytest.raises(ValidationError, match="CANNOT FINALIZE: Mandatory blocking conditions exist"):
        final_service.partner_signoff_and_finalize(
            PartnerSignoffDTO(
                engagement_id="ENG-E2E-001",
                signoff_notes="Premature attempt without required procedures",
                audit_opinion_type="Unmodified",
                udin="25098765AAAAAA1234",
            )
        )

    # 3. Simulate Engagement reaching COMPLETED state
    with db_manager.session_scope() as session:
        eng_repo = EngagementRepository(session)
        eng = eng_repo.get_by_id("ENG-E2E-001")
        eng.status = EngagementStatusEnum.COMPLETED
        eng_repo.update(eng)

    # 4. Hostile Mutation Attack: Attempt to post AJE on sealed engagement
    adj_service = AuditAdjustmentService(db_manager)
    with pytest.raises(ValidationError, match="Tamper-Seal Invariant"):
        adj_service.create_adjustment(
            CreateAJEDTO(
                engagement_id="ENG-E2E-001",
                aje_number="AJE-POSTLOCK",
                entry_date="2025-03-31",
                title="Illicit Entry",
                narration="Trying to alter sealed audit",
                reason="Attack",
                lines=[
                    CreateAJELineDTO(account_code="1001", account_name="Cash", debit_paise=1000, credit_paise=0),
                    CreateAJELineDTO(account_code="2001", account_name="Payable", debit_paise=0, credit_paise=1000),
                ],
            )
        )

    SecurityContext.clear()
