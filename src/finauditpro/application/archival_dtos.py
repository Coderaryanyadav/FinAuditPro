"""Data Transfer Objects (DTOs) for Archival, Readiness Checks, and Reopen Workflows."""

from dataclasses import dataclass, field


@dataclass
class ReadinessItemDTO:
    category: str
    item_name: str
    is_passed: bool
    is_hard_blocker: bool
    details: str


@dataclass
class ReadinessCheckResultDTO:
    engagement_id: str
    is_ready_to_seal: bool
    items: list[ReadinessItemDTO] = field(default_factory=list)
    has_hard_failures: bool = False
    has_soft_warnings: bool = False


@dataclass
class FreezeAndSealDTO:
    engagement_id: str
    sealed_by: str
    report_date: str
    passphrase: str | None = None
    override_justification: str | None = None
    output_dir: str | None = None


@dataclass
class ReopenEngagementDTO:
    engagement_id: str
    reopened_by: str
    user_role: str
    reason: str
