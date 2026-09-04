"""Comprehensive test suite for Form 3CD Tax Audit checks and exception register routing."""

from uuid import uuid4

import pytest

from finauditpro.application.compliance_dtos import RunTaxAuditCheckDTO
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.compliance_service import ComplianceService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.compliance_entities import (
    TaxAuditCategoryEnum,
    TaxAuditCheckResultEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture
def test_setup(tmp_path):
    db_file = tmp_path / "test_tax.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = Firm(id=str(uuid4()), name="Tax Audit Firm LLP", registration_number="REG999")
        firm_repo.add(firm)

        client_repo = ClientRepository(session)
        client = Client(
            id=str(uuid4()), firm_id=firm.id, name="Tax Client Pvt Ltd", industry="Trading"
        )
        client_repo.add(client)

        user_repo = UserRepository(session)
        user = User(
            id=str(uuid4()),
            email="tax_mgr@firm.com",
            username="tax_mgr",
            password_hash="h",
            salt="s",
            full_name="Tax Manager",
            role=RoleEnum.MANAGER,
        )
        user_repo.add(user)

        eng_repo = EngagementRepository(session)
        eng = Engagement(
            id=str(uuid4()),
            firm_id=firm.id,
            client_id=client.id,
            title="FY 2025-26 Tax Audit u/s 44AB",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.TAX_AUDIT,
            status=EngagementStatusEnum.PLANNING,
        )
        eng_repo.add(eng)

    return {"db_manager": db_manager, "engagement_id": eng.id, "user_id": user.id}


def test_tax_audit_checks_execution_and_exception_routing(test_setup) -> None:
    """Verify executing Form 3CD checks and automatic routing of exceptions to AuditException register."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["user_id"], username="tax_mgr", role=RoleEnum.MANAGER)
    )

    comp_service = ComplianceService(db_manager)
    core_service = CoreAuditService(db_manager)

    # 1. Compliant Check: Clause 31 (Section 269SS/T - No cash loans > 20k)
    chk_dto1 = RunTaxAuditCheckDTO(
        engagement_id=eng_id,
        clause_code="Clause 31",
        category=TaxAuditCategoryEnum.LOANS_DEPOSITS_269SS_269T,
        description="Verify acceptance/repayment of loan or deposit in cash exceeding ₹20,000",
        input_source="Ledger Accounts: Unsecured Loans & Director Current Accounts",
        rule_logic="Assert no cash receipt or cash payment entry >= ₹20,000",
        system_result=TaxAuditCheckResultEnum.COMPLIANT,
        exception_amount_paise=0,
        evidence_ref="WP-LOANS-SAMPLE-2026",
    )
    chk1 = comp_service.run_tax_audit_check(chk_dto1)
    assert chk1.system_result == TaxAuditCheckResultEnum.COMPLIANT
    assert chk1.exception_id is None

    # 2. Exception Check: Clause 26 (Section 43B(h) - MSME Overdue Payment of ₹75,000)
    chk_dto2 = RunTaxAuditCheckDTO(
        engagement_id=eng_id,
        clause_code="Clause 26",
        category=TaxAuditCategoryEnum.STATUTORY_DUES_43B,
        description="Amounts inadmissible u/s 43B(h) due to payment beyond 45 days to Micro/Small enterprise",
        input_source="Sundry Creditors Ageing and MSME Udyam Registration Certificates",
        rule_logic="Flag payments to registered MSME suppliers pending > 45 days at year end",
        system_result=TaxAuditCheckResultEnum.EXCEPTION_DETECTED,
        exception_amount_paise=7500000,  # ₹75,000 in paise
        evidence_ref="MSME-OVERDUE-INVOICE-88",
    )
    chk2 = comp_service.run_tax_audit_check(chk_dto2)
    assert chk2.system_result == TaxAuditCheckResultEnum.EXCEPTION_DETECTED
    assert chk2.exception_id is not None
    assert chk2.exception_amount_paise == 7500000

    # 3. Verify that the exception was automatically logged in CoreAuditService
    exceptions = core_service.list_exceptions(eng_id)
    assert len(exceptions) == 1
    assert exceptions[0].amount_paise == 7500000
    assert "43B" in exceptions[0].title

    # 4. Check Tax Audit Summary
    summary = comp_service.get_tax_audit_summary(eng_id)
    assert summary.total_checks == 2
    assert summary.compliant_checks == 1
    assert summary.exception_checks == 1
    assert summary.total_exception_amount_paise == 7500000
    assert summary.is_ready_for_form3cd_signoff is False
