"""Tests for Phase D Completion Checklist, Open Items Register, and Finalization Gate."""

from uuid import uuid4

import pytest

from finauditpro.application.completion_dtos import (
    RelatedPartyCompletionDTO,
    SA240CompletionDTO,
    UpdateChecklistItemDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.engagement_finalization_service import (
    EngagementFinalizationService,
)
from finauditpro.domain.completion_checklist_entities import (
    ChecklistCategoryEnum,
    CompletionStatusEnum,
    ItemSeverityEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.working_paper_entities import (
    ReviewNote,
    ReviewNoteStatusEnum,
    WorkingPaper,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
    WorkingPaperRepository,
)


@pytest.fixture
def completion_env(tmp_path):
    db_file = tmp_path / "test_completion_gate.db"
    db_manager = initialize_database(db_file)
    eng_id = f"eng-chk-{uuid4().hex[:8]}"

    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="partner_gate",
                password_hash="hash",
                salt="salt",
                display_name="CA Partner",
                role=RoleEnum.PARTNER,
            )
        )
        senior = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="senior_gate",
                password_hash="hash",
                salt="salt",
                display_name="CA Senior",
                role=RoleEnum.SENIOR,
            )
        )

        firm = Firm(id="firm-gate", name="Gate Audit LLP")
        FirmRepository(session).add(firm)

        client = Client(
            id="client-gate",
            firm_id=firm.id,
            name="Gate Test Client Pvt Ltd",
            pan_number="AABCG1234F",
            cin_number="U29100MH2020PTC123456",
        )
        ClientRepository(session).add(client)

        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit FY 2025-26",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

    return db_manager, eng_id, partner, senior


def test_completion_checklist_initialization_and_categories(completion_env) -> None:
    db_manager, eng_id, partner, senior = completion_env
    svc = EngagementFinalizationService(db_manager)

    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )

    checklist = svc.get_completion_checklist(eng_id)
    # Verify all 20 standard ICAI categories are represented
    assert len(checklist) == 20
    categories = {item.category for item in checklist}

    expected_categories = {
        ChecklistCategoryEnum.PLANNING.value,
        ChecklistCategoryEnum.RISK_ASSESSMENT.value,
        ChecklistCategoryEnum.AUDIT_PROCEDURES.value,
        ChecklistCategoryEnum.EVIDENCE.value,
        ChecklistCategoryEnum.SAMPLING.value,
        ChecklistCategoryEnum.EXCEPTIONS.value,
        ChecklistCategoryEnum.MISSTATEMENTS.value,
        ChecklistCategoryEnum.REVIEW_NOTES.value,
        ChecklistCategoryEnum.FINANCIAL_STATEMENTS.value,
        ChecklistCategoryEnum.NOTES_AND_DISCLOSURES.value,
        ChecklistCategoryEnum.CASH_FLOW.value,
        ChecklistCategoryEnum.CARO.value,
        ChecklistCategoryEnum.TAX_AUDIT.value,
        ChecklistCategoryEnum.RELATED_PARTIES.value,
        ChecklistCategoryEnum.GOING_CONCERN.value,
        ChecklistCategoryEnum.SUBSEQUENT_EVENTS.value,
        ChecklistCategoryEnum.MANAGEMENT_REPRESENTATION.value,
        ChecklistCategoryEnum.FINAL_ANALYTICAL_REVIEW.value,
        ChecklistCategoryEnum.AUDIT_REPORT.value,
        ChecklistCategoryEnum.PARTNER_REVIEW.value,
    }
    assert expected_categories == categories

    # Verify initial status of all items is NOT_STARTED
    for item in checklist:
        assert item.status == CompletionStatusEnum.NOT_STARTED.value
        assert item.is_applicable is True


def test_checklist_item_update_and_traceability(completion_env) -> None:
    db_manager, eng_id, partner, senior = completion_env
    svc = EngagementFinalizationService(db_manager)

    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )

    checklist = svc.get_completion_checklist(eng_id)
    gc_item = next(i for i in checklist if i.category == ChecklistCategoryEnum.GOING_CONCERN.value)

    # Update item with valid workpaper traceability
    updated = svc.update_checklist_item(
        UpdateChecklistItemDTO(
            engagement_id=eng_id,
            item_id=gc_item.id,
            is_applicable=True,
            status=CompletionStatusEnum.COMPLETE.value,
            supporting_ref="WP-SA570-GC-001",
            reviewer="CA Rahul Mehta",
            notes="Evaluated 12-month projected cash flows; no material uncertainty identified.",
        )
    )

    assert updated.status == CompletionStatusEnum.COMPLETE.value
    assert updated.supporting_ref == "WP-SA570-GC-001"
    assert updated.reviewer == "CA Rahul Mehta"

    # Verify configurable applicability: Set Tax Audit to NOT_APPLICABLE
    tax_item = next(i for i in checklist if i.category == ChecklistCategoryEnum.TAX_AUDIT.value)
    updated_tax = svc.update_checklist_item(
        UpdateChecklistItemDTO(
            engagement_id=eng_id,
            item_id=tax_item.id,
            is_applicable=False,
            status=CompletionStatusEnum.NOT_APPLICABLE.value,
            supporting_ref=None,
            reviewer="CA Rahul Mehta",
            notes="Entity turnover below Section 44AB threshold.",
        )
    )
    assert updated_tax.is_applicable is False
    assert updated_tax.status == CompletionStatusEnum.NOT_APPLICABLE.value


def test_open_items_register_and_severity_classification(completion_env) -> None:
    db_manager, eng_id, partner, senior = completion_env
    svc = EngagementFinalizationService(db_manager)

    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )

    # Add a critical review note on a working paper
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        wp = WorkingPaper(
            id="wp-rev-01",
            engagement_id=eng_id,
            index_reference="WP-REV-001",
            title="Revenue Cut-off Testing",
            area="Revenue",
            status=WorkingPaperStatusEnum.DRAFT,
            preparer_id=senior.id,
        )
        wp_repo.add_working_paper(wp)

        # Unresolved review note
        note = ReviewNote(
            id=str(uuid4()),
            working_paper_id=wp.id,
            raised_by=partner.username,
            note_text="Invoice copies missing for 5 March transactions exceeding performance materiality.",
            status=ReviewNoteStatusEnum.OPEN,
        )
        wp_repo.add_review_note(note)

    open_items = svc.get_open_items_register(eng_id)
    assert open_items.total_open_count > 0
    assert open_items.critical_count >= 1

    # Verify critical item points directly to source
    crit_item = next(i for i in open_items.items if i.severity == ItemSeverityEnum.CRITICAL.value)
    assert "RN-" in crit_item.source_ref
    assert crit_item.is_blocking is True


def test_finalization_gate_blocking_and_explainability(completion_env) -> None:
    db_manager, eng_id, partner, senior = completion_env
    svc = EngagementFinalizationService(db_manager)

    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )

    # Initialize checklist
    svc.get_completion_checklist(eng_id)

    # Evaluate gate on unfinished engagement
    gate = svc.evaluate_finalization_gate(eng_id)
    assert gate.is_ready_for_finalization is False
    assert len(gate.blockers) > 0

    # Ensure every blocker is explainable: category, clear reason, source, action required
    for blocker in gate.blockers:
        assert blocker.category
        assert blocker.reason
        assert blocker.source_ref
        assert blocker.action_required
        assert blocker.severity in (
            ItemSeverityEnum.CRITICAL.value,
            ItemSeverityEnum.HIGH.value,
            ItemSeverityEnum.MEDIUM.value,
            ItemSeverityEnum.LOW.value,
            ItemSeverityEnum.INFORMATIONAL.value,
        )


def test_related_parties_and_sa240_completions(completion_env) -> None:
    db_manager, eng_id, partner, senior = completion_env
    svc = EngagementFinalizationService(db_manager)

    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )

    # Record Related Parties (SA 550) completion
    rp_dto = RelatedPartyCompletionDTO(
        engagement_id=eng_id,
        register_reviewed=True,
        undisclosed_transactions_identified=False,
        arms_length_verified=True,
        schedule_iii_disclosed=True,
        auditor_conclusion="All related party transactions arm's length; Note 28 disclosed.",
        reviewer="CA Senior",
    )
    saved_rp = svc.record_related_party_completion(rp_dto)
    assert saved_rp.register_reviewed is True

    fetched_rp = svc.get_related_party_completion(eng_id)
    assert fetched_rp is not None
    assert fetched_rp.arms_length_verified is True

    # Record SA 240 Management Override completion
    sa240_dto = SA240CompletionDTO(
        engagement_id=eng_id,
        management_override_tested=True,
        journal_entry_testing_completed=True,
        revenue_recognition_presumption_addressed=True,
        risk_indicators_identified=False,
        auditor_conclusion="Mandatory journal entry testing completed under SA 240.",
        reviewer="CA Senior",
    )
    saved_sa240 = svc.record_sa240_completion(sa240_dto)
    assert saved_sa240.journal_entry_testing_completed is True

    fetched_sa240 = svc.get_sa240_completion(eng_id)
    assert fetched_sa240 is not None
    assert fetched_sa240.management_override_tested is True
