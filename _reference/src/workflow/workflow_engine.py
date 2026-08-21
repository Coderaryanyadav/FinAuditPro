"""
Workflow Engine Core State Machine for FinAuditPro.
Manages stage transitions, stage validation execution, event dispatching, and audit progress updating.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .workflow_state import AuditStage, AuditStatus, WorkflowState
from .workflow_validator import WorkflowValidator
from .workflow_events import WorkflowEventManager, WorkflowEvent, EventType
from .workflow_progress import WorkflowProgressTracker
from .workflow_exceptions import StageValidationError, InvalidStageTransitionError

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Core state machine controller for audit engagements.
    Ensures safe, validated stage transitions and dispatches system lifecycle events.
    """

    def __init__(self, event_manager: Optional[WorkflowEventManager] = None):
        self.event_manager = event_manager or WorkflowEventManager()

    def advance_stage(self, state: WorkflowState, target_stage: AuditStage, context_data: Dict[str, Any], user_id: str = "System") -> WorkflowState:
        """
        Advances the audit lifecycle state to target_stage if prerequisites and transitions pass.
        """
        # 1. Validate linear stage transition
        WorkflowValidator.validate_transition(state, target_stage)

        # 2. Validate current stage exit prerequisites
        WorkflowValidator.validate_stage_exit(state, context_data)

        # 3. Perform transition update
        previous_stage = state.current_stage
        state.current_stage = target_stage
        state.completion_percentage = WorkflowProgressTracker.calculate_completion(target_stage)
        state.last_updated = datetime.utcnow()

        if target_stage == AuditStage.AUDIT_COMPLETED:
            state.audit_status = AuditStatus.COMPLETED
            state.completion_date = datetime.utcnow()

        logger.info(f"[STAGE ADVANCE] Engagement {state.engagement_id}: {previous_stage.value} -> {target_stage.value} ({state.completion_percentage}%)")

        # 4. Dispatch domain event
        event_map = {
            AuditStage.CLIENT_CREATED: EventType.CLIENT_CREATED,
            AuditStage.ENGAGEMENT_CREATED: EventType.ENGAGEMENT_CREATED,
            AuditStage.DOCUMENT_COLLECTION: EventType.DOCUMENT_UPLOADED,
            AuditStage.OCR_PROCESSING: EventType.OCR_COMPLETED,
            AuditStage.AI_ANALYSIS: EventType.AI_ANALYSIS_FINISHED,
            AuditStage.RISK_DETECTION: EventType.RISK_UPDATED,
            AuditStage.WORKING_PAPERS_GENERATED: EventType.WORKING_PAPER_CREATED,
            AuditStage.FINAL_REPORT: EventType.REPORT_GENERATED,
            AuditStage.AUDIT_COMPLETED: EventType.AUDIT_COMPLETED,
        }

        if target_stage in event_map:
            event = WorkflowEvent(
                event_type=event_map[target_stage],
                engagement_id=state.engagement_id,
                client_id=state.client_id,
                payload={"previous_stage": previous_stage.value, "new_stage": target_stage.value},
                triggered_by=user_id
            )
            self.event_manager.dispatch(event)

        return state

    def update_reviewer(self, state: WorkflowState, reviewer_name: str) -> WorkflowState:
        """Assign or update current partner/senior reviewer."""
        state.current_reviewer = reviewer_name
        state.last_updated = datetime.utcnow()
        return state

    def mark_blocked(self, state: WorkflowState, block_reason: str) -> WorkflowState:
        """Flag engagement as blocked with a specific task obstacle."""
        if block_reason not in state.blocked_tasks:
            state.blocked_tasks.append(block_reason)
        state.audit_status = AuditStatus.BLOCKED
        state.last_updated = datetime.utcnow()
        return state

    def clear_block(self, state: WorkflowState, block_reason: str) -> WorkflowState:
        """Clear a block obstacle."""
        if block_reason in state.blocked_tasks:
            state.blocked_tasks.remove(block_reason)
        if not state.blocked_tasks:
            state.audit_status = AuditStatus.IN_PROGRESS
        state.last_updated = datetime.utcnow()
        return state
