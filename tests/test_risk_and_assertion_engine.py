"""Tests for Risk Register, SA 315 Categories, Assertion Engine, and Assertion Coverage Matrix."""

import pytest

from finauditpro.application.audit_matrix_dtos import CreateProcedureDTO, CreateRiskDTO
from finauditpro.application.core_audit_dtos import GenerateAssertionCoverageDTO
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    RoleEnum,
    User,
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
    db_path = tmp_path / "test_risk_engine.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(id="firm-1", name="CA Audit Firm"))
        user_repo = UserRepository(session)
        user_repo.add(
            User(id="user-auditor", username="auditor1", password_hash="h", salt="s", role="Senior")
        )
        client = ClientRepository(session).add(
            Client(id="client-1", firm_id=firm.id, name="ABC Manufacturing Pvt Ltd")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                id="eng-1",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        return eng


def test_risk_classification_and_assertion_linking(db_manager, seed_engagement):
    """Verify risks can be created across SA 315 categories with multi-assertion linking."""
    matrix_svc = AuditMatrixService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    # 1. Financial Statement Level / Fraud Risk
    risk_fraud = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=seed_engagement.id,
            risk_code="RSK-REV-001",
            title="Management Override in Revenue Recognition",
            category="Revenue from Operations",
            description="Risk of fictitious invoicing near balance sheet date to inflate EBITDA",
            assertions=[AssertionEnum.OCCURRENCE, AssertionEnum.CUT_OFF],
            inherent_risk=RiskSeverityEnum.HIGH,
            control_risk=RiskSeverityEnum.MEDIUM,
            severity=RiskSeverityEnum.HIGH,
            is_significant_risk=True,
            risk_response="Perform substantive test of cutoff and examine journal entries",
        )
    )
    assert risk_fraud.id is not None
    assert risk_fraud.derived_romm == RiskSeverityEnum.HIGH
    assert AssertionEnum.OCCURRENCE in risk_fraud.assertions
    assert AssertionEnum.CUT_OFF in risk_fraud.assertions

    # 2. Control / IT Risk
    risk_it = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=seed_engagement.id,
            risk_code="RSK-IT-002",
            title="ERP User Access Controls Weakness",
            category="IT-related Risk",
            description="Segregation of duties deficiency in inventory write-off authorization",
            assertions=[AssertionEnum.VALUATION, AssertionEnum.COMPLETENESS],
            inherent_risk=RiskSeverityEnum.MEDIUM,
            control_risk=RiskSeverityEnum.HIGH,
            severity=RiskSeverityEnum.HIGH,
            is_significant_risk=False,
            risk_response="Perform direct substantive stock valuation testing without control reliance",
        )
    )
    assert risk_it.id is not None
    assert risk_it.derived_romm == RiskSeverityEnum.HIGH


def test_assertion_coverage_matrix_and_gap_detection(db_manager, seed_engagement):
    """Verify Assertion Coverage Matrix accurately identifies covered areas and audit gaps."""
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-auditor", username="auditor1", role=RoleEnum.SENIOR)
    )

    # Create Risk in PPE area
    risk = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=seed_engagement.id,
            risk_code="RSK-PPE-001",
            title="Unrecorded Asset Retirements",
            category="Property, Plant and Equipment",
            description="Impairment and physical existence of plant machinery",
            assertions=[AssertionEnum.EXISTENCE, AssertionEnum.VALUATION],
            inherent_risk=RiskSeverityEnum.MEDIUM,
            control_risk=RiskSeverityEnum.LOW,
            severity=RiskSeverityEnum.MEDIUM,
        )
    )

    # Create Procedure addressing PPE Existence
    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=seed_engagement.id,
            linked_risk_ids=[risk.id],
            procedure_code="PRC-PPE-001",
            objective="Physical inspection of major plant additions during the year",
            assertions=[AssertionEnum.EXISTENCE],
            procedure_type="Substantive Test",
            instructions="Sample fixed asset register items and inspect physically on shop floor",
        )
    )

    # Generate Coverage Matrix
    rep = core_svc.generate_assertion_coverage_matrix(
        GenerateAssertionCoverageDTO(engagement_id=seed_engagement.id)
    )
    assert rep.total_matrix_lines >= 6
    assert rep.gap_count > 0  # Identifies areas lacking risks or procedures

    # Locate PPE Existence line -> Has risk and procedure
    ppe_exist_line = next(
        l
        for l in rep.lines
        if l.account_or_area == "Property, Plant and Equipment"
        and l.assertion == AssertionEnum.EXISTENCE
    )
    assert "RSK-PPE-001" in ppe_exist_line.linked_risk_codes
    assert "PRC-PPE-001" in ppe_exist_line.linked_procedure_codes
