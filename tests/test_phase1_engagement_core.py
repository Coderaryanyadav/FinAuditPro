"""Phase 1 Automated Verification Suite — Engagement-Centric Core.

Validates:
1. Engagement entity fields (partner, manager, team, start_date, reporting_date, version, properties).
2. State machine transitions across full lifecycle (DRAFT -> ACCEPTANCE -> PLANNING -> FIELDWORK -> REVIEW -> FINALISATION -> COMPLETED -> ARCHIVED).
3. Rejection of illegal state transitions.
4. Engagement-level data isolation.
5. Tamper-seal & locked engagement protection.
6. Engagement Dashboard aggregation metrics.
"""

import pytest
from sqlalchemy.orm import Session

from finauditpro.application.dtos import (
    CreateClientDTO,
    CreateEngagementDTO,
    CreateFirmDTO,
    UpdateEngagementDTO,
)
from finauditpro.application.security.engagement_lock_guard import assert_engagement_not_locked
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
)
from finauditpro.domain.engagement_state_machine import EngagementStateMachine
from finauditpro.domain.exceptions import (
    InvalidStateTransitionError,
    ValidationError,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import (
    AuditFindingModel,
    AuditRiskModel,
    DocumentModel,
    FinancialDatasetModel,
    MaterialityAssessmentModel,
)
from finauditpro.infrastructure.persistence.pbc_and_query_models import (
    ClientDocumentRequestModel,
)
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)
from finauditpro.infrastructure.persistence.working_paper_models import (
    ReviewNoteModel,
    WorkingPaperModel,
)


@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "phase1_test.db"
    manager = DatabaseManager(db_path=db_file)
    manager.create_tables()
    return manager


@pytest.fixture
def setup_firm_and_client(db_manager):
    with db_manager.session_scope() as session:
        firm_repo = FirmRepository(session)
        client_repo = ClientRepository(session)

        firm = firm_repo.add(
            Firm(
                name="S.R. Batliboi & Associates",
                registration_number="FRN-101049W",
                pan="AAAFS1234F",
            )
        )
        client = client_repo.add(
            Client(
                firm_id=firm.id,
                name="Tata Motors Commercial Solutions Ltd",
                pan="AAACT1234K",
            )
        )
        return firm.id, client.id


class TestEngagementEntityAndProperties:
    """Test pure domain engagement model, properties, and validation."""

    def test_engagement_entity_fields_and_aliases(self):
        eng = Engagement(
            firm_id="firm-1",
            client_id="client-1",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.DRAFT,
            partner="CA Rajesh Sharma",
            manager="Amit Verma",
            assigned_team=["Senior Auditor", "Associate 1"],
            start_date="2025-04-01",
            reporting_date="2025-09-30",
            version=1,
        )
        assert eng.engagement_id == eng.id
        assert eng.engagement_type == AuditTypeEnum.STATUTORY_AUDIT
        assert eng.team == ["Senior Auditor", "Associate 1"]
        assert eng.partner == "CA Rajesh Sharma"
        assert eng.manager == "Amit Verma"
        assert eng.start_date == "2025-04-01"
        assert eng.reporting_date == "2025-09-30"
        assert eng.version == 1

    def test_engagement_empty_fy_validation(self):
        with pytest.raises((ValidationError, Exception)):
            Engagement(
                firm_id="firm-1",
                client_id="client-1",
                financial_year="",
            )


class TestEngagementStateMachine:
    """Test state machine valid and invalid lifecycle transitions."""

    def test_full_valid_lifecycle(self):
        eng = Engagement(
            firm_id="firm-1",
            client_id="client-1",
            financial_year="2025-26",
            status=EngagementStatusEnum.DRAFT,
        )

        lifecycle = [
            EngagementStatusEnum.ACCEPTANCE,
            EngagementStatusEnum.PLANNING,
            EngagementStatusEnum.FIELDWORK,
            EngagementStatusEnum.REVIEW,
            EngagementStatusEnum.FINALISATION,
            EngagementStatusEnum.COMPLETED,
            EngagementStatusEnum.ARCHIVED,
        ]

        for next_state in lifecycle:
            assert EngagementStateMachine.can_transition(eng.status, next_state) is True
            eng.transition_to(next_state)
            assert eng.status == next_state

    def test_reopen_archived_engagement(self):
        eng = Engagement(
            firm_id="firm-1",
            client_id="client-1",
            financial_year="2025-26",
            status=EngagementStatusEnum.ARCHIVED,
        )
        assert EngagementStateMachine.can_transition(eng.status, EngagementStatusEnum.REOPENED) is True
        eng.transition_to(EngagementStatusEnum.REOPENED)
        assert eng.status == EngagementStatusEnum.REOPENED

    @pytest.mark.parametrize(
        "current_state,illegal_target",
        [
            (EngagementStatusEnum.DRAFT, EngagementStatusEnum.COMPLETED),
            (EngagementStatusEnum.DRAFT, EngagementStatusEnum.ARCHIVED),
            (EngagementStatusEnum.DRAFT, EngagementStatusEnum.FINALISATION),
            (EngagementStatusEnum.ACCEPTANCE, EngagementStatusEnum.COMPLETED),
            (EngagementStatusEnum.PLANNING, EngagementStatusEnum.COMPLETED),
            (EngagementStatusEnum.PLANNING, EngagementStatusEnum.ARCHIVED),
            (EngagementStatusEnum.FIELDWORK, EngagementStatusEnum.ARCHIVED),
            (EngagementStatusEnum.FIELDWORK, EngagementStatusEnum.COMPLETED),
            (EngagementStatusEnum.ARCHIVED, EngagementStatusEnum.PLANNING),
            (EngagementStatusEnum.ARCHIVED, EngagementStatusEnum.FIELDWORK),
            (EngagementStatusEnum.ARCHIVED, EngagementStatusEnum.DRAFT),
        ],
    )
    def test_invalid_transitions_rejected(self, current_state, illegal_target):
        eng = Engagement(
            firm_id="firm-1",
            client_id="client-1",
            financial_year="2025-26",
            status=current_state,
        )
        assert EngagementStateMachine.can_transition(current_state, illegal_target) is False
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            eng.transition_to(illegal_target)
        assert "Cannot transition Engagement" in str(exc_info.value)


class TestEngagementServiceAndLifecycle:
    """Test application layer engagement creation, state transitions, and dashboard."""

    def test_create_and_update_engagement_service(self, db_manager, setup_firm_and_client):
        firm_id, client_id = setup_firm_and_client
        service = EngagementService(db_manager)

        create_dto = CreateEngagementDTO(
            firm_id=firm_id,
            client_id=client_id,
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.DRAFT,
            partner="CA Rajesh Sharma",
            manager="Amit Verma",
            assigned_team=["Senior 1", "Associate 1"],
            start_date="2025-04-01",
            reporting_date="2025-09-30",
        )
        created = service.create_engagement(create_dto)
        assert created.id is not None
        assert created.partner == "CA Rajesh Sharma"
        assert created.status == EngagementStatusEnum.DRAFT
        assert created.version == 1

        # Transition to Acceptance
        transitioned = service.transition_engagement_status(
            created.id, EngagementStatusEnum.ACCEPTANCE, actor="Engagement Partner"
        )
        assert transitioned.status == EngagementStatusEnum.ACCEPTANCE
        assert transitioned.version == 2

        # Transition to Planning
        service.transition_engagement_status(created.id, EngagementStatusEnum.PLANNING)
        fetched = service.get_engagement(created.id)
        assert fetched.status == EngagementStatusEnum.PLANNING

    def test_illegal_transition_in_service_raises(self, db_manager, setup_firm_and_client):
        firm_id, client_id = setup_firm_and_client
        service = EngagementService(db_manager)

        created = service.create_engagement(
            CreateEngagementDTO(
                firm_id=firm_id,
                client_id=client_id,
                financial_year="2025-26",
                status=EngagementStatusEnum.DRAFT,
            )
        )

        with pytest.raises(InvalidStateTransitionError):
            service.transition_engagement_status(created.id, EngagementStatusEnum.COMPLETED)

        with pytest.raises(InvalidStateTransitionError):
            service.update_engagement(
                created.id, UpdateEngagementDTO(status=EngagementStatusEnum.ARCHIVED)
            )

    def test_engagement_dashboard_aggregation(self, db_manager, setup_firm_and_client):
        firm_id, client_id = setup_firm_and_client
        service = EngagementService(db_manager)

        eng = service.create_engagement(
            CreateEngagementDTO(
                firm_id=firm_id,
                client_id=client_id,
                financial_year="2025-26",
                status=EngagementStatusEnum.FIELDWORK,
                partner="CA Ananya Roy",
                reporting_date="2025-10-31",
            )
        )

        # Seed working papers, review notes, findings, risks, and materiality in database
        with db_manager.session_scope() as session:
            # 2 Working papers: 1 Completed, 1 Draft
            session.add(
                WorkingPaperModel(
                    id="wp-1",
                    engagement_id=eng.id,
                    index_reference="WP-REV-01",
                    title="Revenue Substantive Cut-off",
                    area="Revenue",
                    status="Partner Approved",
                    preparer_id="staff-1",
                    conclusion="Satisfactory",
                )
            )
            session.add(
                WorkingPaperModel(
                    id="wp-2",
                    engagement_id=eng.id,
                    index_reference="WP-FA-01",
                    title="Fixed Assets Physical Verification",
                    area="Fixed Assets",
                    status="Draft",
                    preparer_id="staff-1",
                    conclusion="",
                )
            )
            session.flush()
            # 1 Open Review Note
            session.add(
                ReviewNoteModel(
                    id="rn-1",
                    working_paper_id="wp-2",
                    raised_by="mgr-1",
                    note_text="Verify title deeds of immovable property",
                    status="Open",
                )
            )
            # 1 Outstanding PBC request
            session.add(
                ClientDocumentRequestModel(
                    id="pbc-1",
                    engagement_id=eng.id,
                    title="Bank Confirmation FY25",
                    description="Bank statement and confirmation balance",
                    status="Pending",
                )
            )
            # 1 High Risk
            session.add(
                AuditRiskModel(
                    id="risk-1",
                    engagement_id=eng.id,
                    risk_code="RSK-01",
                    title="Related Party Unapproved Loans",
                    category="Statutory Compliance",
                    description="Loans to directors under Sec 185",
                    derived_romm="High",
                    is_significant_risk=1,
                )
            )
            # 1 Open Finding
            session.add(
                AuditFindingModel(
                    id="find-1",
                    engagement_id=eng.id,
                    title="Unreconciled ITC Difference in GSTR-2B",
                    description="Excess ITC claimed of Rs 4,50,000",
                    amount_paise=45000000,
                    status="Open",
                )
            )
            # Materiality
            session.add(
                MaterialityAssessmentModel(
                    id="mat-1",
                    engagement_id=eng.id,
                    benchmark_type="1% of Turnover",
                    benchmark_amount_paise=10000000000,
                    overall_percentage=1.0,
                    overall_materiality_paise=100000000,  # 10 Lakhs
                    performance_percentage=75.0,
                    performance_materiality_paise=75000000,
                    clearly_trivial_threshold_paise=5000000,
                )
            )
            # Financial Dataset
            session.add(
                FinancialDatasetModel(
                    id="ds-1",
                    engagement_id=eng.id,
                    dataset_name="FY25 Trial Balance Final",
                    dataset_type="Trial Balance",
                    file_path="/data/tb.xlsx",
                    content_hash="hash-1234",
                    row_count=150,
                )
            )

        # Retrieve Dashboard
        dashboard = service.get_engagement_dashboard(eng.id)

        assert dashboard.engagement_id == eng.id
        assert dashboard.financial_year == "2025-26"
        assert dashboard.total_working_papers == 2
        assert dashboard.open_working_papers == 1
        assert dashboard.completion_percentage == 50.0
        assert dashboard.open_review_notes == 1
        assert dashboard.outstanding_pbc == 1
        assert dashboard.unresolved_findings == 1
        assert "Related Party Unapproved Loans" in dashboard.high_risk_areas
        assert dashboard.materiality_overall_paise == 100000000
        assert dashboard.materiality_performance_paise == 75000000
        assert dashboard.tb_balanced is True
        assert dashboard.reporting_date == "2025-10-31"
        assert "Blocked (1 open review notes)" in dashboard.finalisation_status


class TestEngagementIsolationAndLocking:
    """Test strict data partitioning between engagements and locking guards."""

    def test_cross_engagement_isolation(self, db_manager, setup_firm_and_client):
        firm_id, client_id = setup_firm_and_client
        service = EngagementService(db_manager)

        eng1 = service.create_engagement(
            CreateEngagementDTO(
                firm_id=firm_id,
                client_id=client_id,
                financial_year="2024-25",
                status=EngagementStatusEnum.COMPLETED,
            )
        )
        eng2 = service.create_engagement(
            CreateEngagementDTO(
                firm_id=firm_id,
                client_id=client_id,
                financial_year="2025-26",
                status=EngagementStatusEnum.PLANNING,
            )
        )

        with db_manager.session_scope() as session:
            session.add(
                WorkingPaperModel(
                    id="wp-eng1",
                    engagement_id=eng1.id,
                    index_reference="WP-REV-01",
                    title="FY24 Revenue WP",
                    area="Revenue",
                    status="Locked",
                    preparer_id="p1",
                    conclusion="Done",
                )
            )
            session.add(
                WorkingPaperModel(
                    id="wp-eng2",
                    engagement_id=eng2.id,
                    index_reference="WP-REV-02",
                    title="FY25 Revenue WP",
                    area="Revenue",
                    status="Draft",
                    preparer_id="p1",
                    conclusion="WIP",
                )
            )

        dash1 = service.get_engagement_dashboard(eng1.id)
        dash2 = service.get_engagement_dashboard(eng2.id)

        assert dash1.total_working_papers == 1
        assert dash1.open_working_papers == 0
        assert dash1.completion_percentage == 100.0

        assert dash2.total_working_papers == 1
        assert dash2.open_working_papers == 1
        assert dash2.completion_percentage == 0.0

    def test_locked_engagement_mutation_guard(self):
        locked_eng = Engagement(
            firm_id="firm-1",
            client_id="client-1",
            financial_year="2024-25",
            status=EngagementStatusEnum.COMPLETED,
        )
        with pytest.raises(ValidationError) as exc:
            assert_engagement_not_locked(locked_eng)
        assert "Tamper-Seal Invariant" in str(exc.value)

        archived_eng = Engagement(
            firm_id="firm-1",
            client_id="client-1",
            financial_year="2023-24",
            status=EngagementStatusEnum.ARCHIVED,
        )
        with pytest.raises(ValidationError) as exc2:
            assert_engagement_not_locked(archived_eng)
        assert "Tamper-Seal Invariant" in str(exc2.value)

        # Active engagement passes
        active_eng = Engagement(
            firm_id="firm-1",
            client_id="client-1",
            financial_year="2025-26",
            status=EngagementStatusEnum.FIELDWORK,
        )
        assert_engagement_not_locked(active_eng)  # should not raise
