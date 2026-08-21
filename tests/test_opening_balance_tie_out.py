"""Unit tests for SA 510 opening balance tie-out math in paise, mismatch detection, and auditor confirmation."""

import pytest
from finauditpro.application.roll_forward_dtos import ConfirmTieOutDTO
from finauditpro.domain.roll_forward_entities import OpeningBalanceLink, calculate_opening_tie_out
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import RollForwardRepository


@pytest.fixture
def setup_tieout_env(tmp_path):
    db_file = tmp_path / "test_tieout_m10.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    return db_manager


def test_calculate_opening_tie_out_matched() -> None:
    """Verify tie-out calculation marks matched account figures in paise as tied out."""
    links = [
        OpeningBalanceLink(
            engagement_id="eng-new",
            source_engagement_id="eng-old",
            account_code="1001",
            account_name="Cash",
            opening_dr_paise=500000,
            opening_cr_paise=0,
            prior_closing_dr_paise=500000,
            prior_closing_cr_paise=0,
        ),
        OpeningBalanceLink(
            engagement_id="eng-new",
            source_engagement_id="eng-old",
            account_code="2001",
            account_name="Payables",
            opening_dr_paise=0,
            opening_cr_paise=500000,
            prior_closing_dr_paise=0,
            prior_closing_cr_paise=500000,
        ),
    ]

    summary = calculate_opening_tie_out(links)
    assert summary.total_accounts == 2
    assert summary.tied_out_accounts == 2
    assert summary.mismatched_accounts == 0
    assert summary.is_fully_tied_out is True
    assert summary.verified_statutory is False  # Requires auditor confirmation


def test_calculate_opening_tie_out_mismatched() -> None:
    """Verify tie-out calculation flags mismatch when opening DR/CR does not match prior closing."""
    links = [
        OpeningBalanceLink(
            engagement_id="eng-new",
            source_engagement_id="eng-old",
            account_code="1001",
            account_name="Cash",
            opening_dr_paise=500000,  # Opening = Rs 5000
            opening_cr_paise=0,
            prior_closing_dr_paise=450000,  # Prior closing = Rs 4500 (Mismatch!)
            prior_closing_cr_paise=0,
        )
    ]

    summary = calculate_opening_tie_out(links)
    assert summary.total_accounts == 1
    assert summary.tied_out_accounts == 0
    assert summary.mismatched_accounts == 1
    assert summary.is_fully_tied_out is False


def test_confirm_opening_balance_tie_out_persistence(setup_tieout_env) -> None:
    """Verify auditor confirmation updates database records and flags auditor verification."""
    db_manager = setup_tieout_env

    from finauditpro.application.services.firm_service import FirmService, CreateFirmDTO
    from finauditpro.application.services.client_service import ClientService, CreateClientDTO
    from finauditpro.application.services.engagement_service import EngagementService, CreateEngagementDTO

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="TieOut Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="TieOut Client"))
    eng_prior = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2024-25"))
    eng_confirm = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26"))

    link = OpeningBalanceLink(
        engagement_id=eng_confirm.id,
        source_engagement_id=eng_prior.id,
        account_code="1002",
        account_name="Bank",
        opening_dr_paise=100000,
        opening_cr_paise=0,
        prior_closing_dr_paise=100000,
        prior_closing_cr_paise=0,
        is_tied_out=True,
    )

    with db_manager.session_scope() as session:
        repo = RollForwardRepository(session)
        repo.add_opening_balance_links([link])

    with db_manager.session_scope() as session:
        repo = RollForwardRepository(session)
        repo.confirm_opening_balance_tie_out(eng_confirm.id, "Lead Auditor", "2026-04-01T10:00:00Z")

    with db_manager.session_scope() as session:
        repo = RollForwardRepository(session)
        fetched = repo.list_opening_balance_links(eng_confirm.id)
        assert len(fetched) == 1
        assert fetched[0].is_verified_by_auditor is True
        assert fetched[0].verified_by == "Lead Auditor"
