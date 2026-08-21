"""
Workflow Progress Tracker & KPI Engine for FinAuditPro.
Calculates audit completion percentages, remaining stages, next steps, and dashboard metrics.
"""

from typing import Dict, Any, List
from .workflow_state import AuditStage, WorkflowState, AuditStatus

class WorkflowProgressTracker:
    """
    Computes precise progress metrics, completion ratios, and next-step guidance for auditors.
    """

    @classmethod
    def calculate_completion(cls, current_stage: AuditStage) -> float:
        """
        Calculate weighted completion percentage based on stage order (16 stages total).
        """
        stages = AuditStage.stage_order()
        total_stages = len(stages) - 1  # 15 steps (0 to 15)
        current_index = current_stage.get_index()

        percentage = (current_index / total_stages) * 100.0
        return round(min(percentage, 100.0), 2)

    @classmethod
    def get_progress_summary(cls, state: WorkflowState) -> Dict[str, Any]:
        """
        Generate comprehensive progress report for UI dashboards and progress bars.
        """
        stages = AuditStage.stage_order()
        current_index = state.current_stage.get_index()

        completed_steps = [s.value for s in stages[:current_index]]
        current_step = state.current_stage.value
        next_step = stages[current_index + 1].value if current_index + 1 < len(stages) else "AUDIT_COMPLETED"

        remaining_stages = [s.value for s in stages[current_index + 1:]]
        completion_pct = cls.calculate_completion(state.current_stage)

        return {
            "engagement_id": state.engagement_id,
            "current_stage": current_step,
            "completed_steps_count": len(completed_steps),
            "total_steps_count": len(stages),
            "completion_percentage": completion_pct,
            "next_step": next_step,
            "completed_steps": completed_steps,
            "remaining_stages": remaining_stages,
            "pending_tasks": list(state.pending_tasks),
            "blocked_tasks": list(state.blocked_tasks),
            "audit_status": state.audit_status.value,
            "current_reviewer": state.current_reviewer or "Unassigned",
        }
