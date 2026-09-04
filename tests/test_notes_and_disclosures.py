"""Comprehensive test suite for Notes to Accounts, Disclosures, Accounting Policies, and Data Lineage."""

from uuid import uuid4

import pytest

from finauditpro.application.financial_statement_dtos import (
    CreateOrUpdateNoteDTO,
    CreateOrUpdatePolicyDTO,
    GetDataLineageDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.financial_statement_service import FinancialStatementService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.financial_entities import (
    DatasetTypeEnum,
    FinancialDataset,
    TrialBalanceLine,
)
from finauditpro.domain.financial_statement_entities import DisclosureClassificationEnum
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture
def test_setup(tmp_path):
    db_file = tmp_path / "test_notes.db"
    db_manager = initialize_database(db_file)

    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        firm = Firm(id=str(uuid4()), name="Audit Firm LLP", registration_number="REG123")
        firm_repo.add(firm)

        client_repo = ClientRepository(session)
        client = Client(
            id=str(uuid4()), firm_id=firm.id, name="Notes Client Pvt Ltd", industry="Manufacturing"
        )
        client_repo.add(client)

        user_repo = UserRepository(session)
        user = User(
            id=str(uuid4()),
            email="senior@firm.com",
            username="senior_user",
            password_hash="h",
            salt="s",
            full_name="Senior Auditor",
            role=RoleEnum.SENIOR,
        )
        user_repo.add(user)

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

        dataset_id = str(uuid4())
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(
            FinancialDataset(
                id=dataset_id,
                engagement_id=eng.id,
                dataset_name="Trial Balance",
                dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
                filename="tb.csv",
            )
        )

        tb_lines = [
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=1,
                account_code="4003A",
                account_name="Trade Debtors North",
                closing_dr_paise=30000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=2,
                account_code="4003B",
                account_name="Trade Debtors South",
                closing_dr_paise=20000000,
            ),
            TrialBalanceLine(
                dataset_id=dataset_id,
                source_row_no=3,
                account_code="1001",
                account_name="Equity Capital",
                closing_cr_paise=50000000,
            ),
        ]
        fin_repo.add_trial_balance_lines(tb_lines)

    map_service = AccountMappingService(db_manager)
    map_service.initialize_mappings_from_trial_balance(eng.id, dataset_id)
    map_service.update_mapping(
        eng.id,
        "4003A",
        "Trade Receivables",
        "Trade Receivables - Undisputed Good",
        "WP-G1",
        AccountTypeEnum.ASSET,
        "Debtors North",
    )
    map_service.update_mapping(
        eng.id,
        "4003B",
        "Trade Receivables",
        "Trade Receivables - Undisputed Good",
        "WP-G1",
        AccountTypeEnum.ASSET,
        "Debtors South",
    )
    map_service.update_mapping(
        eng.id,
        "1001",
        "Share Capital",
        "Equity Share Capital",
        "WP-A1",
        AccountTypeEnum.EQUITY,
        "Share Capital",
    )

    return {"db_manager": db_manager, "engagement_id": eng.id, "user_id": user.id}


def test_structured_notes_and_accounting_policies(test_setup) -> None:
    """Verify creating structured notes with 5-tier classification and accounting policies."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["user_id"], username="senior_user", role=RoleEnum.SENIOR)
    )

    fs_service = FinancialStatementService(db_manager)

    # 1. Add Note to Accounts
    note_dto = CreateOrUpdateNoteDTO(
        engagement_id=eng_id,
        note_number="Note 16",
        title="Trade Receivables Breakdown",
        fs_reference="Balance Sheet Line CA-02",
        source_type="Mapped TB Accounts",
        disclosure_classification=DisclosureClassificationEnum.AUTOMATIC,
        amount_paise=50000000,
        details=[
            {"code": "4003A", "name": "Trade Debtors North", "amount_paise": 30000000},
            {"code": "4003B", "name": "Trade Debtors South", "amount_paise": 20000000},
        ],
        narrative="Undisputed trade receivables considered good, aged less than 6 months.",
    )
    note = fs_service.create_or_update_note(note_dto)
    assert note.note_number == "Note 16"
    assert note.amount_paise == 50000000
    assert note.disclosure_classification == DisclosureClassificationEnum.AUTOMATIC
    assert len(note.details) == 2

    # 2. Add Accounting Policy
    pol_dto = CreateOrUpdatePolicyDTO(
        engagement_id=eng_id,
        policy_code="POL-01",
        title="Revenue Recognition Policy",
        category="Revenue",
        applicable_standard="AS 9 / Ind AS 115",
        policy_text="Revenue is recognized upon transfer of control and dispatch of goods to customers.",
        changes_text="No changes during the reporting period.",
    )
    policy = fs_service.create_or_update_policy(pol_dto)
    assert policy.policy_code == "POL-01"
    assert policy.applicable_standard == "AS 9 / Ind AS 115"
    assert policy.status == "Approved"


def test_deterministic_data_lineage_trace(test_setup) -> None:
    """Verify deterministic lineage tracing for a Balance Sheet line item."""
    db_manager = test_setup["db_manager"]
    eng_id = test_setup["engagement_id"]

    SecurityContext.set_current_session(
        UserSession(user_id=test_setup["user_id"], username="senior_user", role=RoleEnum.SENIOR)
    )

    fs_service = FinancialStatementService(db_manager)

    # Add Note 16 first
    fs_service.create_or_update_note(
        CreateOrUpdateNoteDTO(
            engagement_id=eng_id,
            note_number="Note 16",
            title="Trade Receivables Breakdown",
            fs_reference="Balance Sheet Line CA-02",
            amount_paise=50000000,
        )
    )

    # Trace CA-02 (Trade Receivables)
    lineage = fs_service.get_data_lineage(
        GetDataLineageDTO(engagement_id=eng_id, line_code="CA-02")
    )
    assert lineage.fs_line_code == "CA-02"
    assert lineage.fs_line_name == "Trade Receivables"
    assert lineage.total_amount_paise == 50000000
    assert lineage.note_ref == "Note 16"
    assert len(lineage.account_traces) == 2
    assert {"4003A", "4003B"} == {t["account_code"] for t in lineage.account_traces}
