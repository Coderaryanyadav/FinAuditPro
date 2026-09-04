"""Central security guard enforcing engagement finalization and immutability invariants."""

from typing import Any

from finauditpro.domain.entities import EngagementStatusEnum
from finauditpro.domain.exceptions import ValidationError


def assert_engagement_not_locked(engagement: Any) -> None:
    """Verifies that an engagement is not completed or archived before allowing mutations.

    Raises ValidationError if the engagement is finalized or locked.
    """
    if engagement is None:
        return

    status = getattr(engagement, "status", None)
    if status is None:
        return

    status_val = status.value if hasattr(status, "value") else str(status)
    if status_val in (EngagementStatusEnum.COMPLETED.value, EngagementStatusEnum.ARCHIVED.value, "Completed", "Archived"):
        eng_id = getattr(engagement, "id", "UNKNOWN")
        raise ValidationError(
            f"Tamper-Seal Invariant: Engagement '{eng_id}' is finalized and cryptographically locked "
            f"(Status: {status_val}). Further modifications, postings, deletions, or uploads are strictly prohibited."
        )
