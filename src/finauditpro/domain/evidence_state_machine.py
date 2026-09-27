"""Domain state machine and integrity verification for Audit Evidence."""

import hashlib
from pathlib import Path

from finauditpro.domain.audit_matrix_entities import EvidenceStatusEnum
from finauditpro.domain.exceptions import InvalidStateTransitionError, ValidationError


VALID_EVIDENCE_TRANSITIONS: dict[EvidenceStatusEnum, set[EvidenceStatusEnum]] = {
    EvidenceStatusEnum.UPLOADED: {
        EvidenceStatusEnum.VALIDATING,
        EvidenceStatusEnum.VALIDATED,
        EvidenceStatusEnum.REJECTED,
    },
    EvidenceStatusEnum.VALIDATING: {
        EvidenceStatusEnum.VALIDATED,
        EvidenceStatusEnum.REJECTED,
        EvidenceStatusEnum.UPLOADED,
    },
    EvidenceStatusEnum.VALIDATED: {
        EvidenceStatusEnum.LINKED,
        EvidenceStatusEnum.REVIEWED,
        EvidenceStatusEnum.REJECTED,
    },
    EvidenceStatusEnum.LINKED: {
        EvidenceStatusEnum.REVIEWED,
        EvidenceStatusEnum.VALIDATED,
        EvidenceStatusEnum.REJECTED,
    },
    EvidenceStatusEnum.REVIEWED: {
        EvidenceStatusEnum.ACCEPTED,
        EvidenceStatusEnum.REJECTED,
        EvidenceStatusEnum.LINKED,
    },
    EvidenceStatusEnum.ACCEPTED: {
        EvidenceStatusEnum.REVIEWED,
    },
    EvidenceStatusEnum.REJECTED: {
        EvidenceStatusEnum.REVIEWED,
        EvidenceStatusEnum.VALIDATED,
    },
}

REVIEW_ROLES = {"partner", "manager", "senior auditor", "lead auditor", "reviewer"}


def calculate_stream_sha256(file_path: Path | str, chunk_size: int = 65536) -> str:
    """Calculate cryptographic SHA-256 hash using chunked streaming for large files."""
    path = Path(file_path)
    if not path.is_file():
        raise ValidationError(f"Evidence file not found: {file_path}")
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


class EvidenceStateMachine:
    """State machine governing evidence lifecycle and role-based permissions."""

    @staticmethod
    def transition(
        current_status: EvidenceStatusEnum,
        target_status: EvidenceStatusEnum,
        actor_role: str = "Auditor",
    ) -> EvidenceStatusEnum:
        if current_status == target_status:
            return current_status

        allowed = VALID_EVIDENCE_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise InvalidStateTransitionError("AuditEvidence", current_status.value, target_status.value)

        # Permission check: Only review roles can transition to ACCEPTED or REJECTED
        if target_status in (EvidenceStatusEnum.ACCEPTED, EvidenceStatusEnum.REJECTED):
            norm_role = actor_role.strip().lower()
            if not any(r in norm_role for r in REVIEW_ROLES):
                raise ValidationError(f"Role '{actor_role}' does not have permission to approve or reject audit evidence.")

        return target_status
