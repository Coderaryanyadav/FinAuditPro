"""Tests for Phase 0.5 Engagement-Centric Kernel.

Validates:
1. Canonical hierarchy (Firm -> Client -> Engagement -> Financial Year)
2. EngagementStateMachine transition validation, roles, metadata, and side effects
3. Centralized EngagementContext isolation, subscriptions, and scope validation
4. Real domain queries for dashboard metrics without hardcoded zeros
5. Cross-engagement isolation enforcement
"""

import pytest

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.engagement_context import EngagementContext, EngagementContextState, current_context
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_request_service import DocumentRequestService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import AuditTypeEnum, EngagementStatusEnum, RoleEnum
from finauditpro.domain.engagement_state_machine import EngagementStateMachine
from finauditpro.domain.exceptions import InvalidStateTransitionError, ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def db_manager(tmp_path):
    db_path = tmp_path / "test_kernel.db"
    mgr = DatabaseManager(db_path=db_path)
    mgr.create_tables()
    return mgr


@pytest.fixture
def setup_services(db_manager):
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    pbc_svc = DocumentRequestService(db_manager)
    return firm_svc, client_svc, eng_svc, pbc_svc


class TestEngagementStateMachineKernel:
    """Validate rich state machine transitions, metadata, and invariants."""

    def test_canonical_lifecycle_path(self):
        """Test the standard linear audit lifecycle path."""
        # DRAFT -> ACCEPTANCE -> PLANNING -> FIELDWORK -> REVIEW -> FINALISATION -> COMPLETED -> ARCHIVED
        path = [
            (EngagementStatusEnum.DRAFT, EngagementStatusEnum.ACCEPTANCE),
            (EngagementStatusEnum.ACCEPTANCE, EngagementStatusEnum.PLANNING),
            (EngagementStatusEnum.PLANNING, EngagementStatusEnum.FIELDWORK),
            (EngagementStatusEnum.FIELDWORK, EngagementStatusEnum.REVIEW),
            (EngagementStatusEnum.REVIEW, EngagementStatusEnum.FINALISATION),
            (EngagementStatusEnum.FINALISATION, EngagementStatusEnum.COMPLETED),
            (EngagementStatusEnum.COMPLETED, EngagementStatusEnum.ARCHIVED),
        ]
        for src, tgt in path:
            assert EngagementStateMachine.can_transition(src, tgt), f"Failed for {src} -> {tgt}"
            meta = EngagementStateMachine.validate_transition(src, tgt)
            assert meta is not None
            assert meta.source_status == src
            assert meta.target_status == tgt
            assert len(meta.allowed_actors) > 0
            assert len(meta.preconditions) > 0
            assert len(meta.side_effects) > 0
            assert len(meta.audit_event_action) > 0

    def test_invalid_lifecycle_skips_rejected(self):
        """Test illegal status transitions are strictly rejected."""
        illegal_transitions = [
            (EngagementStatusEnum.DRAFT, EngagementStatusEnum.COMPLETED),
            (EngagementStatusEnum.DRAFT, EngagementStatusEnum.ARCHIVED),
            (EngagementStatusEnum.ACCEPTANCE, EngagementStatusEnum.REVIEW),
            (EngagementStatusEnum.PLANNING, EngagementStatusEnum.COMPLETED),
            (EngagementStatusEnum.FIELDWORK, EngagementStatusEnum.ARCHIVED),
            (EngagementStatusEnum.ARCHIVED, EngagementStatusEnum.PLANNING),
        ]
        for src, tgt in illegal_transitions:
            assert not EngagementStateMachine.can_transition(src, tgt)
            with pytest.raises(InvalidStateTransitionError):
                EngagementStateMachine.validate_transition(src, tgt)

    def test_role_based_transition_permissions(self):
        """Test that unauthorized actors are blocked from privileged transitions."""
        # Only Partner or Admin can seal an engagement to ARCHIVED
        with pytest.raises(ValidationError) as exc:
            EngagementStateMachine.validate_transition(
                EngagementStatusEnum.COMPLETED,
                EngagementStatusEnum.ARCHIVED,
                actor_role=RoleEnum.ASSOCIATE,
            )
        assert "unauthorized" in str(exc.value).lower()

        # Partner is permitted
        meta = EngagementStateMachine.validate_transition(
            EngagementStatusEnum.COMPLETED,
            EngagementStatusEnum.ARCHIVED,
            actor_role=RoleEnum.PARTNER,
        )
        assert meta.target_status == EngagementStatusEnum.ARCHIVED

    def test_reopen_workflow_metadata(self):
        """Test reopening archived engagements carries judicial/peer-review justification requirements."""
        meta = EngagementStateMachine.get_metadata(
            EngagementStatusEnum.ARCHIVED, EngagementStatusEnum.REOPENED
        )
        assert meta is not None
        assert "NFRA" in meta.preconditions or "ICAI" in meta.preconditions
        assert "tamper" in meta.side_effects.lower() or "cryptographic" in meta.side_effects.lower()


class TestEngagementContext:
    """Validate centralized EngagementContext singleton behavior."""

    def test_context_lifecycle_and_subscription(self):
        ctx = EngagementContext()
        ctx.clear()
        assert not ctx.state.is_active
        assert ctx.state.display_title == "No Active Engagement"

        events_received = []

        def on_change(state: EngagementContextState):
            events_received.append(state.engagement_id)

        sub_id = ctx.subscribe(on_change)

        ctx.set_context(
            firm_id="FIRM-01",
            firm_name="S. Raman & Co.",
            client_id="CLI-01",
            client_name="Tata Consultancy Services",
            engagement_id="ENG-01",
            financial_year="2025-26",
            engagement_type="Statutory Audit",
            status="Planning",
        )

        assert ctx.state.is_active
        assert "Tata Consultancy Services" in ctx.state.display_title
        assert "2025-26" in ctx.state.display_title
        assert len(events_received) == 1
        assert events_received[0] == "ENG-01"

        ctx.update_status("Fieldwork")
        assert ctx.state.status == "Fieldwork"
        assert len(events_received) == 2

        ctx.unsubscribe(sub_id)
        ctx.clear()
        assert not ctx.state.is_active
        assert len(events_received) == 2  # No more notifications after unsubscribe

    def test_engagement_isolation_validation(self):
        ctx = EngagementContext()
        ctx.set_context(
            firm_id="FIRM-01",
            firm_name="Firm A",
            client_id="CLI-01",
            client_name="Client A",
            engagement_id="ENG-ALPHA",
            financial_year="2025-26",
        )

        # Accessing matching engagement passes
        ctx.validate_engagement_id("ENG-ALPHA")

        # Accessing mismatched engagement raises isolation error
        with pytest.raises(ValidationError) as exc:
            ctx.validate_engagement_id("ENG-BETA")
        assert "Engagement isolation violation" in str(exc.value)


class TestEngagementCentricServices:
    """Validate end-to-end service interactions with real domain queries."""

    def test_dashboard_summary_live_queries_without_hardcoded_zeros(self, setup_services):
        firm_svc, client_svc, eng_svc, pbc_svc = setup_services

        firm = firm_svc.create_firm(CreateFirmDTO(name="Mehta & Associates CA"))
        client = client_svc.create_client(
            CreateClientDTO(firm_id=firm.id, name="Reliance Infrastructure Ltd")
        )
        eng = eng_svc.create_engagement(
            CreateEngagementDTO(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )

        # Initial dashboard summary
        summary = eng_svc.get_dashboard_summary(firm_id=firm.id)
        assert summary.total_clients == 1
        assert summary.active_engagements == 1
        assert summary.pending_documents == 0

        # Create a pending PBC document request
        pbc_svc.create_request(
            engagement_id=eng.id,
            title="Signed Board Minutes FY 2025-26",
            description="Certified copy of board meeting minutes approving financial statements",
            due_date="2026-04-15",
        )

        # Re-query dashboard summary to verify pending_documents reflects real count
        updated_summary = eng_svc.get_dashboard_summary(firm_id=firm.id)
        assert updated_summary.pending_documents == 1

    def test_engagement_lifecycle_transition_and_audit_logging(self, setup_services):
        firm_svc, client_svc, eng_svc, _ = setup_services

        firm = firm_svc.create_firm(CreateFirmDTO(name="Goel & Co."))
        client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Infosys Ltd"))
        eng = eng_svc.create_engagement(
            CreateEngagementDTO(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )

        # Transition PLANNING -> FIELDWORK
        transitioned = eng_svc.transition_engagement_status(
            engagement_id=eng.id,
            new_status=EngagementStatusEnum.FIELDWORK,
            actor="Engagement Partner",
        )
        assert transitioned.status == EngagementStatusEnum.FIELDWORK

        # Check engagement dashboard
        dash = eng_svc.get_engagement_dashboard(eng.id)
        assert dash.status == "Fieldwork"
        assert dash.client_name == "Infosys Ltd"
        assert dash.firm_name == "Goel & Co."
        assert not dash.is_locked
