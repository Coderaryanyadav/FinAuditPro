"""Engagement lifecycle state machine for FinAuditPro.

Manages valid and invalid transitions across all audit engagement stages:
DRAFT -> ACCEPTANCE -> PLANNING -> FIELDWORK -> REVIEW -> FINALISATION -> COMPLETED -> ARCHIVED

For every transition, defines:
- Permitted Actor roles (SQC 1 / SA 220)
- Preconditions
- Side effects
- Audit event taxonomy
"""

from dataclasses import dataclass, field
from enum import StrEnum

from finauditpro.domain.entities import EngagementStatusEnum, RoleEnum
from finauditpro.domain.exceptions import InvalidStateTransitionError, ValidationError


@dataclass(frozen=True)
class TransitionMetadata:
    source_status: EngagementStatusEnum
    target_status: EngagementStatusEnum
    allowed_actors: tuple[RoleEnum, ...]
    preconditions: str
    side_effects: str
    audit_event_action: str


# Canonical transition rules with metadata
_TRANSITION_REGISTRY: dict[tuple[EngagementStatusEnum, EngagementStatusEnum], TransitionMetadata] = {
    (EngagementStatusEnum.DRAFT, EngagementStatusEnum.ACCEPTANCE): TransitionMetadata(
        source_status=EngagementStatusEnum.DRAFT,
        target_status=EngagementStatusEnum.ACCEPTANCE,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.ADMIN),
        preconditions="Client profile created with valid PAN/GSTIN and KYC information.",
        side_effects="Initiates client acceptance & independence evaluation checklist.",
        audit_event_action="Engagement Submitted for Client Acceptance",
    ),
    (EngagementStatusEnum.DRAFT, EngagementStatusEnum.PLANNING): TransitionMetadata(
        source_status=EngagementStatusEnum.DRAFT,
        target_status=EngagementStatusEnum.PLANNING,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.ADMIN),
        preconditions="Direct planning transition approved by Engagement Partner.",
        side_effects="Scaffolds preliminary audit program and materiality assessment.",
        audit_event_action="Engagement Moved Directly to Planning",
    ),
    (EngagementStatusEnum.ACCEPTANCE, EngagementStatusEnum.PLANNING): TransitionMetadata(
        source_status=EngagementStatusEnum.ACCEPTANCE,
        target_status=EngagementStatusEnum.PLANNING,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="Independence declaration verified; engagement letter issued (SA 210).",
        side_effects="Unlocks materiality workbench and risk register.",
        audit_event_action="Client Acceptance Approved — Planning Commenced",
    ),
    (EngagementStatusEnum.ACCEPTANCE, EngagementStatusEnum.DRAFT): TransitionMetadata(
        source_status=EngagementStatusEnum.ACCEPTANCE,
        target_status=EngagementStatusEnum.DRAFT,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.ADMIN),
        preconditions="Engagement terms rejected or returned for modification.",
        side_effects="Resets acceptance checklist.",
        audit_event_action="Engagement Returned to Draft from Acceptance",
    ),
    (EngagementStatusEnum.PLANNING, EngagementStatusEnum.FIELDWORK): TransitionMetadata(
        source_status=EngagementStatusEnum.PLANNING,
        target_status=EngagementStatusEnum.FIELDWORK,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.ADMIN),
        preconditions="SA 320 materiality established; SA 315 risk matrix documented; TB staged.",
        side_effects="Enables substantive procedure execution and working paper scaffolding.",
        audit_event_action="Audit Planning Approved — Fieldwork Unlocked",
    ),
    (EngagementStatusEnum.PLANNING, EngagementStatusEnum.DRAFT): TransitionMetadata(
        source_status=EngagementStatusEnum.PLANNING,
        target_status=EngagementStatusEnum.DRAFT,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="Engagement planning aborted or scope cancelled.",
        side_effects="Flags planning records as provisional.",
        audit_event_action="Engagement Returned to Draft from Planning",
    ),
    (EngagementStatusEnum.FIELDWORK, EngagementStatusEnum.REVIEW): TransitionMetadata(
        source_status=EngagementStatusEnum.FIELDWORK,
        target_status=EngagementStatusEnum.REVIEW,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.SENIOR, RoleEnum.ADMIN),
        preconditions="All scheduled substantive procedures executed; draft findings documented.",
        side_effects="Submits working papers to Manager/Partner review drawer.",
        audit_event_action="Fieldwork Completed — Submitted for Manager/Partner Review",
    ),
    (EngagementStatusEnum.FIELDWORK, EngagementStatusEnum.PLANNING): TransitionMetadata(
        source_status=EngagementStatusEnum.FIELDWORK,
        target_status=EngagementStatusEnum.PLANNING,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.ADMIN),
        preconditions="Material scope revision or new high-risk area identified during testing.",
        side_effects="Reopens risk matrix for amendment.",
        audit_event_action="Fieldwork Reopened for Additional Planning",
    ),
    (EngagementStatusEnum.REVIEW, EngagementStatusEnum.FINALISATION): TransitionMetadata(
        source_status=EngagementStatusEnum.REVIEW,
        target_status=EngagementStatusEnum.FINALISATION,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="All Review Notes CLEARED; SA 450 misstatements evaluated against materiality.",
        side_effects="Locks all individual working papers; enables draft report generation.",
        audit_event_action="Review Cleared — Finalisation Gate Unlocked",
    ),
    (EngagementStatusEnum.REVIEW, EngagementStatusEnum.FIELDWORK): TransitionMetadata(
        source_status=EngagementStatusEnum.REVIEW,
        target_status=EngagementStatusEnum.FIELDWORK,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.ADMIN),
        preconditions="Open review notes require additional fieldwork/testing.",
        side_effects="Returns working paper to preparer for amendment.",
        audit_event_action="Review Returned for Additional Fieldwork",
    ),
    (EngagementStatusEnum.FINALISATION, EngagementStatusEnum.COMPLETED): TransitionMetadata(
        source_status=EngagementStatusEnum.FINALISATION,
        target_status=EngagementStatusEnum.COMPLETED,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="Statutory audit report signed by Engagement Partner with UDIN/DSC.",
        side_effects="Seals engagement database partition; starts SQC 1 60-day archival countdown.",
        audit_event_action="Engagement Completed and Audit Opinion Issued",
    ),
    (EngagementStatusEnum.FINALISATION, EngagementStatusEnum.REVIEW): TransitionMetadata(
        source_status=EngagementStatusEnum.FINALISATION,
        target_status=EngagementStatusEnum.REVIEW,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="Partner review note raised on draft audit report or financial disclosures.",
        side_effects="Unlocks draft report editor.",
        audit_event_action="Finalisation Returned to Review",
    ),
    (EngagementStatusEnum.COMPLETED, EngagementStatusEnum.ARCHIVED): TransitionMetadata(
        source_status=EngagementStatusEnum.COMPLETED,
        target_status=EngagementStatusEnum.ARCHIVED,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="SQC 1 retention package generated with SHA-256 manifest.",
        side_effects="Marks entire engagement immutable and read-only.",
        audit_event_action="Audit Engagement Sealed and Archived (SQC 1)",
    ),
    (EngagementStatusEnum.COMPLETED, EngagementStatusEnum.FINALISATION): TransitionMetadata(
        source_status=EngagementStatusEnum.COMPLETED,
        target_status=EngagementStatusEnum.FINALISATION,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="Subsequent event requiring report amendment before archival.",
        side_effects="Reopens finalisation gate with partner audit trail.",
        audit_event_action="Completed Engagement Reopened for Subsequent Events",
    ),
    (EngagementStatusEnum.ARCHIVED, EngagementStatusEnum.REOPENED): TransitionMetadata(
        source_status=EngagementStatusEnum.ARCHIVED,
        target_status=EngagementStatusEnum.REOPENED,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="NFRA / ICAI Peer Review / Judicial subpoena override reason provided.",
        side_effects="Logs cryptographic tamper record; increments engagement version.",
        audit_event_action="Archived Engagement Formally Reopened with Justification",
    ),
    (EngagementStatusEnum.REOPENED, EngagementStatusEnum.ARCHIVED): TransitionMetadata(
        source_status=EngagementStatusEnum.REOPENED,
        target_status=EngagementStatusEnum.ARCHIVED,
        allowed_actors=(RoleEnum.PARTNER, RoleEnum.ADMIN),
        preconditions="Reopened review completed and re-sealed.",
        side_effects="Re-computes package SHA-256 seal manifest.",
        audit_event_action="Reopened Engagement Re-Archived and Re-Sealed",
    ),
}

# Add alias transitions for backwards-compatibility
_ALIASES = {
    EngagementStatusEnum.DOCUMENT_COLLECTION: EngagementStatusEnum.FIELDWORK,
    EngagementStatusEnum.FINANCIAL_ANALYSIS: EngagementStatusEnum.FIELDWORK,
    EngagementStatusEnum.AUDIT_PROCEDURES: EngagementStatusEnum.FIELDWORK,
    EngagementStatusEnum.FINALIZING: EngagementStatusEnum.FINALISATION,
}


class EngagementStateMachine:
    """Pure domain state machine governing engagement lifecycle transitions."""

    @classmethod
    def can_transition(
        cls, current_status: EngagementStatusEnum | str, target_status: EngagementStatusEnum | str
    ) -> bool:
        """Check if transition from current_status to target_status is permissible."""
        curr_enum = cls._to_enum(current_status)
        target_enum = cls._to_enum(target_status)

        if curr_enum == target_enum:
            return True

        if (curr_enum, target_enum) in _TRANSITION_REGISTRY:
            return True

        # Check resolved canonical aliases
        norm_curr = _ALIASES.get(curr_enum, curr_enum)
        norm_target = _ALIASES.get(target_enum, target_enum)
        if norm_curr == norm_target:
            return True

        return (norm_curr, norm_target) in _TRANSITION_REGISTRY

    @classmethod
    def validate_transition(
        cls,
        current_status: EngagementStatusEnum | str,
        target_status: EngagementStatusEnum | str,
        actor_role: RoleEnum | None = None,
    ) -> TransitionMetadata:
        """Validate state transition; raises InvalidStateTransitionError if illegal."""
        curr_enum = cls._to_enum(current_status)
        target_enum = cls._to_enum(target_status)

        if curr_enum == target_enum:
            return TransitionMetadata(
                source_status=curr_enum,
                target_status=target_enum,
                allowed_actors=(RoleEnum.PARTNER, RoleEnum.MANAGER, RoleEnum.SENIOR, RoleEnum.ASSOCIATE, RoleEnum.ADMIN),
                preconditions="Self-transition (no state change).",
                side_effects="None.",
                audit_event_action="No-op status verification",
            )

        norm_curr = _ALIASES.get(curr_enum, curr_enum)
        norm_target = _ALIASES.get(target_enum, target_enum)

        meta = _TRANSITION_REGISTRY.get((curr_enum, target_enum)) or _TRANSITION_REGISTRY.get((norm_curr, norm_target))
        if not meta:
            raise InvalidStateTransitionError(
                entity_type="Engagement",
                current_state=curr_enum.value,
                target_state=target_enum.value,
            )

        if actor_role is not None and actor_role not in meta.allowed_actors:
            raise ValidationError(
                f"Role '{actor_role.value}' is unauthorized to transition engagement from '{curr_enum.value}' to '{target_enum.value}'. "
                f"Permitted roles: {[r.value for r in meta.allowed_actors]}"
            )

        return meta

    @classmethod
    def get_metadata(
        cls, current_status: EngagementStatusEnum | str, target_status: EngagementStatusEnum | str
    ) -> TransitionMetadata | None:
        """Retrieve transition metadata for a pair of statuses."""
        curr_enum = cls._to_enum(current_status)
        target_enum = cls._to_enum(target_status)
        norm_curr = _ALIASES.get(curr_enum, curr_enum)
        norm_target = _ALIASES.get(target_enum, target_enum)
        return _TRANSITION_REGISTRY.get((curr_enum, target_enum)) or _TRANSITION_REGISTRY.get((norm_curr, norm_target))

    @classmethod
    def get_allowed_transitions(
        cls, current_status: EngagementStatusEnum | str
    ) -> list[EngagementStatusEnum]:
        """Return list of allowed target statuses from current status."""
        curr_enum = cls._to_enum(current_status)
        norm_curr = _ALIASES.get(curr_enum, curr_enum)

        targets = set()
        for (src, tgt) in _TRANSITION_REGISTRY.keys():
            if src == curr_enum or src == norm_curr:
                targets.add(tgt)

        return sorted(list(targets), key=lambda s: s.value)

    @staticmethod
    def _to_enum(status: EngagementStatusEnum | str) -> EngagementStatusEnum:
        if isinstance(status, EngagementStatusEnum):
            return status
        for s in EngagementStatusEnum:
            if s.value.lower() == str(status).lower() or s.name.lower() == str(status).lower():
                return s
        return EngagementStatusEnum(status)
