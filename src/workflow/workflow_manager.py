"""
Workflow Manager & State Persistence Manager for FinAuditPro.
Provides active engagement context tracking, crash recovery, database state sync, and dashboard metrics.
"""

from typing import Dict, Any, Optional, List
import logging

from .workflow_state import AuditStage, AuditStatus, WorkflowState
from .workflow_engine import WorkflowEngine
from .workflow_events import WorkflowEventManager, WorkflowEvent, EventType
from .workflow_progress import WorkflowProgressTracker
from .workflow_validator import WorkflowValidator
from .workflow_exceptions import WorkflowStateCorruptedError

logger = logging.getLogger(__name__)

import threading

class WorkflowManager:
    """
    Facade and orchestrator for active engagement workflow state persistence,
    recovery after application restarts, and cross-module context coordination.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(WorkflowManager, cls).__new__(cls)
                    cls._instance._engine = WorkflowEngine()
                    cls._instance._event_manager = WorkflowEventManager()
                    cls._instance._active_state: Optional[WorkflowState] = None
                    cls._instance._state_cache: Dict[int, WorkflowState] = {}
        return cls._instance

    @property
    def current_state(self) -> Optional[WorkflowState]:
        """Returns the currently selected/active engagement workflow state."""
        return self._active_state

    def initialize_engagement(self, engagement_id: int, client_id: int, financial_year: str) -> WorkflowState:
        """Create and initialize a new audit workflow state."""
        state = WorkflowState(
            engagement_id=engagement_id,
            client_id=client_id,
            financial_year=financial_year,
            current_stage=AuditStage.ENGAGEMENT_CREATED,
            audit_status=AuditStatus.IN_PROGRESS,
            completion_percentage=WorkflowProgressTracker.calculate_completion(AuditStage.ENGAGEMENT_CREATED)
        )
        self._state_cache[engagement_id] = state
        self._active_state = state
        logger.info(f"Initialized Workflow State for Engagement {engagement_id}")
        return state

    def load_engagement_state(self, engagement_id: int, saved_data: Optional[Dict[str, Any]] = None) -> WorkflowState:
        """
        Load or recover engagement state from storage/cache.
        """
        if engagement_id in self._state_cache:
            state = self._state_cache[engagement_id]
            self._active_state = state
            return state

        if saved_data:
            try:
                state = WorkflowState.from_dict(saved_data)
                self._state_cache[engagement_id] = state
                self._active_state = state
                logger.info(f"Recovered Workflow State for Engagement {engagement_id} at stage {state.current_stage.value}")
                return state
            except Exception as e:
                raise WorkflowStateCorruptedError(f"Failed to recover workflow state for engagement {engagement_id}: {e}")

        raise WorkflowStateCorruptedError(f"No state found or cached for engagement ID {engagement_id}")

    def set_active_engagement(self, engagement_id: int) -> WorkflowState:
        """Set the active engagement by ID if cached."""
        if engagement_id in self._state_cache:
            self._active_state = self._state_cache[engagement_id]
            return self._active_state
        raise WorkflowStateCorruptedError(f"Engagement {engagement_id} is not loaded in memory.")

    def advance_current_stage(self, target_stage: AuditStage, context_data: Dict[str, Any], user_id: str = "System") -> WorkflowState:
        """Advance the active engagement's stage."""
        if not self._active_state:
            raise WorkflowStateCorruptedError("No active engagement loaded in WorkflowManager.")

        updated_state = self._engine.advance_stage(self._active_state, target_stage, context_data, user_id)
        self._state_cache[updated_state.engagement_id] = updated_state
        self._active_state = updated_state
        return updated_state

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Retrieves active engagement metrics specifically formatted for Dashboard UI integration.
        """
        if not self._active_state:
            return {
                "active_engagement": False,
                "engagement_id": None,
                "current_stage": "No Active Engagement",
                "completion_percentage": 0.0,
                "audit_status": AuditStatus.NOT_STARTED.value,
                "pending_reviews": 0,
                "pending_documents": 0,
            }

        progress_summary = WorkflowProgressTracker.get_progress_summary(self._active_state)
        return {
            "active_engagement": True,
            "engagement_id": self._active_state.engagement_id,
            "client_id": self._active_state.client_id,
            "financial_year": self._active_state.financial_year,
            "current_stage": self._active_state.current_stage.value,
            "completion_percentage": self._active_state.completion_percentage,
            "audit_status": self._active_state.audit_status.value,
            "current_reviewer": self._active_state.current_reviewer or "Unassigned",
            "progress_summary": progress_summary
        }
