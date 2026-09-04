"""Comprehensive test suite for CARO 2020 20-clause working paper lifecycle and review."""

from uuid import uuid4

import pytest

from finauditpro.application.compliance_dtos import (
    ExecuteCAROProcedureDTO,
    ReviewCAROClauseDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.compliance_service import ComplianceService
from finauditpro.domain.compliance_entities import (
    CAROApplicabilityEnum,
    CAROReportAnswerEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.exceptions import PermissionDeniedError
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture
def test_setup(tmp_path):
    db_file = tmp_path / "test_caro.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = Firm(id=str(uuid4()), name="Audit Firm LLP", registration_number="REG123")
        firm_repo.add(firm)

        client_repo = ClientRepository(session)
        client = Client(
            id=str(uuid4()), firm_id=firm.id, name="CARO Client Ltd", industry="Manufacturing"
        )
        client_repo.add(client)

        user_repo = UserRepository(session)
        senior = User(
            id=str(uuid4()),
            email="senior@firm.com",
            username="senior_user",
            password_hash="h",
            salt="s",
            full_name="Senior Auditor",
            role=RoleEnum.SENIOR,
        )
        assoc = User(
            id=str(uuid4()),
            email="assoc@firm.com",
            username="assoc_user",
            password_hash="h",
            salt="s",
            full_name="Junior Associate",
            role=RoleEnum.ASSOCIATE,
        )
        user_repo.add(senior)
        user_repo.add(assoc)

        eng_repo = EngagementRepository(session)
        eng = Engagement(
            id=str(uuid4()),
            firm_id=firm.id,
            client_id=client.id,
            title="FY 2025-26 Statutory Audit",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.PLANNING,
        )
        eng_repo.add(eng)

    return {
        "db_manager": db_manager,
        "engagement_id": eng.id,
        "senior_id": senior.id,
        "assoc_id": assoc.id,
    }


def test_caro_initialization_and_procedure_execution(test_setup) -> None:
    """Verify initialization of all 20 CARO 2020 clauses and execution of specific clause procedures."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["senior_id"], username="senior_user", role=RoleEnum.SENIOR)
    )

    comp_service = ComplianceService(db_manager)

    # 1. Initialize all 20 standard CARO clauses
    clauses = comp_service.initialize_caro_clauses(eng_id)
    assert len(clauses) == 20
    assert any(c.clause_code == "3(i)" for c in clauses)
    assert any(c.clause_code == "3(ii)" for c in clauses)
    assert any(c.clause_code == "3(vii)" for c in clauses)
    assert any(c.clause_code == "3(xx)" for c in clauses)

    # 2. Execute Clause 3(i) (PPE & Intangibles)
    exec_dto = ExecuteCAROProcedureDTO(
        engagement_id=eng_id,
        clause_code="3(i)",
        clause_title="Property, Plant & Equipment and Intangible Assets",
        applicability=CAROApplicabilityEnum.APPLICABLE,
        applicability_reason="Company holds ₹15 Cr in manufacturing plant and title deeds",
        question="Whether proper records of PPE are maintained and title deeds held in company name?",
        procedure_text="Inspected fixed asset register, verified physical inspection reports by management, and inspected title deeds for all 3 land parcels.",
        evidence_refs=["DOC-FAR-2026", "DOC-TITLE-LAND-01"],
        management_response="All title deeds are in company name and registered with Registrar of Sub-Assurances.",
        conclusion_text="Title deeds and fixed asset register fully verified and reconciled without discrepancies.",
        report_answer=CAROReportAnswerEnum.UNQUALIFIED,
    )
    wp = comp_service.execute_caro_procedure(exec_dto)
    assert wp.clause_code == "3(i)"
    assert wp.status == "Completed"
    assert wp.report_answer == CAROReportAnswerEnum.UNQUALIFIED
    assert len(wp.evidence_refs) == 2

    # 3. Review CARO Clause by Senior
    rev_dto = ReviewCAROClauseDTO(
        engagement_id=eng_id,
        clause_code="3(i)",
        decision="APPROVE",
        reviewer_notes="FAR sample verified.",
    )
    reviewed_wp = comp_service.review_caro_clause(rev_dto)
    assert reviewed_wp.status == "Reviewed"
    assert reviewed_wp.reviewer == "senior_user"


def test_caro_review_rbac_enforcement(test_setup) -> None:
    """Verify that an Associate cannot review or approve a CARO clause working paper."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    comp_service = ComplianceService(db_manager)
    comp_service.initialize_caro_clauses(eng_id)

    # Associate attempt
    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["assoc_id"], username="assoc_user", role=RoleEnum.ASSOCIATE)
    )

    with pytest.raises(
        PermissionDeniedError, match="Only Senior, Manager, or Partner can review CARO workpapers"
    ):
        comp_service.review_caro_clause(
            ReviewCAROClauseDTO(engagement_id=eng_id, clause_code="3(i)", decision="APPROVE")
        )
