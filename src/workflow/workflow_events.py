"""
Workflow Event System for FinAuditPro.
Provides asynchronous event dispatching, audit logging integration, notification triggers, and subscriber hooks.
"""

import uuid
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Domain Audit Lifecycle Event Types."""
    CLIENT_CREATED = "ClientCreated"
    ENGAGEMENT_CREATED = "EngagementCreated"
    DOCUMENT_UPLOADED = "DocumentUploaded"
    OCR_COMPLETED = "OCRCompleted"
    AI_ANALYSIS_FINISHED = "AIAnalysisFinished"
    FINDING_GENERATED = "FindingGenerated"
    RISK_UPDATED = "RiskUpdated"
    WORKING_PAPER_CREATED = "WorkingPaperCreated"
    REPORT_GENERATED = "ReportGenerated"
    AUDIT_COMPLETED = "AuditCompleted"


@dataclass
class WorkflowEvent:
    """Represents a domain audit event."""
    event_type: EventType
    engagement_id: int
    client_id: int
    payload: Dict[str, Any] = field(default_factory=dict)
    triggered_by: str = "System"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)


class WorkflowEventManager:
    """
    Centralized Event Dispatcher & Listener Registry (Observer Pattern).
    Dispatches events asynchronously to audit loggers, notifications, and dashboard hooks.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WorkflowEventManager, cls).__new__(cls)
            cls._instance._listeners: Dict[EventType, List[Callable[[WorkflowEvent], None]]] = {}
            cls._instance._event_history: List[WorkflowEvent] = []
        return cls._instance

    def subscribe(self, event_type: EventType, callback: Callable[[WorkflowEvent], None]) -> None:
        """Register a subscriber callback for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.info(f"Subscribed callback to event: {event_type.value}")

    def dispatch(self, event: WorkflowEvent) -> None:
        """Dispatch event to all registered listeners and log event."""
        self._event_history.append(event)
        logger.info(f"[EVENT DISPATCH] {event.event_type.value} | Engagement: {event.engagement_id} | User: {event.triggered_by}")

        # Notify direct subscribers
        callbacks = self._listeners.get(event.event_type, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event listener for {event.event_type.value}: {e}", exc_info=True)

    def get_history(self, engagement_id: int = None) -> List[WorkflowEvent]:
        """Retrieve event history, optionally filtered by engagement ID."""
        if engagement_id:
            return [e for e in self._event_history if e.engagement_id == engagement_id]
        return list(self._event_history)
