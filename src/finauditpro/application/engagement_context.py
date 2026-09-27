"""Centralized Engagement Context Manager for FinAuditPro.

Maintains the active hierarchical context:
Firm -> Client -> Engagement -> Financial Year

Provides engagement isolation, subscriber notification, and scope validation.
"""

from dataclasses import dataclass
from typing import Any, Callable
from uuid import uuid4

from finauditpro.domain.exceptions import ValidationError


@dataclass
class EngagementContextState:
    firm_id: str | None = None
    firm_name: str | None = None
    client_id: str | None = None
    client_name: str | None = None
    engagement_id: str | None = None
    financial_year: str | None = None
    engagement_type: str | None = None
    status: str | None = None
    partner: str | None = None
    manager: str | None = None
    version: int = 1

    @property
    def is_active(self) -> bool:
        """Returns True if a valid engagement is actively selected."""
        return bool(self.engagement_id and self.client_id and self.firm_id)

    @property
    def display_title(self) -> str:
        """Formatted summary of the active engagement."""
        if not self.is_active:
            return "No Active Engagement"
        return f"{self.client_name or 'Client'} · FY {self.financial_year or 'N/A'} · {self.engagement_type or 'Audit'}"


class EngagementContext:
    """Thread-safe, observable singleton managing the current engagement context."""

    _instance: "EngagementContext | None" = None

    def __new__(cls) -> "EngagementContext":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._state = EngagementContextState()
            cls._instance._listeners = {}
        return cls._instance

    @property
    def state(self) -> EngagementContextState:
        return self._state

    def set_context(
        self,
        firm_id: str,
        firm_name: str,
        client_id: str,
        client_name: str,
        engagement_id: str,
        financial_year: str,
        engagement_type: str = "Statutory Audit",
        status: str = "Planning",
        partner: str | None = None,
        manager: str | None = None,
        version: int = 1,
    ) -> EngagementContextState:
        """Set the active engagement context and notify subscribers."""
        if not firm_id or not client_id or not engagement_id:
            raise ValidationError("firm_id, client_id, and engagement_id are mandatory for context.")

        self._state = EngagementContextState(
            firm_id=firm_id,
            firm_name=firm_name,
            client_id=client_id,
            client_name=client_name,
            engagement_id=engagement_id,
            financial_year=financial_year,
            engagement_type=engagement_type,
            status=status,
            partner=partner,
            manager=manager,
            version=version,
        )
        self._notify_listeners()
        return self._state

    def update_status(self, new_status: str) -> None:
        """Update the active engagement status in-place and notify subscribers."""
        if self._state.is_active:
            self._state.status = new_status
            self._notify_listeners()

    def clear(self) -> None:
        """Clear active context when switching firms or logging out."""
        self._state = EngagementContextState()
        self._notify_listeners()

    def validate_engagement_id(self, engagement_id: str) -> None:
        """Enforce engagement isolation; raises ValidationError if accessing mismatched engagement."""
        if not self._state.is_active:
            return
        if self._state.engagement_id != engagement_id:
            raise ValidationError(
                f"Engagement isolation violation: active context is '{self._state.engagement_id}', "
                f"attempted access on '{engagement_id}'."
            )

    def subscribe(self, callback: Callable[[EngagementContextState], Any]) -> str:
        """Register a callback for context change events. Returns subscriber ID."""
        sub_id = str(uuid4())
        self._listeners[sub_id] = callback
        return sub_id

    def unsubscribe(self, sub_id: str) -> None:
        """Unregister a subscriber callback."""
        self._listeners.pop(sub_id, None)

    def _notify_listeners(self) -> None:
        for callback in list(self._listeners.values()):
            try:
                callback(self._state)
            except Exception:
                pass


# Global singleton instance access
current_context = EngagementContext()
