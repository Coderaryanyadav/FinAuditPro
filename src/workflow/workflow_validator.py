"""
Workflow Validation Engine for FinAuditPro.
Enforces business rules and prerequisite checks before stage transitions or domain operations.
"""

from typing import Dict, Any, List, Optional
from .workflow_state import AuditStage, WorkflowState
from .workflow_exceptions import StageValidationError, PrerequisiteNotMetError, InvalidStageTransitionError

class WorkflowValidator:
    """
    Validates stage transitions, prerequisite constraints, and exit criteria.
    Ensures auditors cannot jump ahead or bypass statutory quality controls.
    """

    # Stage exit criteria requirements
    STAGE_PREREQUISITES: Dict[AuditStage, List[str]] = {
        AuditStage.CLIENT_CREATED: ["client_id"],
        AuditStage.FINANCIAL_YEAR_SELECTED: ["financial_year"],
        AuditStage.ENGAGEMENT_CREATED: ["engagement_id", "audit_type"],
        AuditStage.MATERIALITY_DEFINED: ["materiality_threshold"],
        AuditStage.DOCUMENT_COLLECTION: ["document_count"],
        AuditStage.OCR_PROCESSING: ["ocr_completed_count"],
        AuditStage.DOCUMENT_CLASSIFICATION: ["classified_docs"],
        AuditStage.AI_ANALYSIS: ["ai_findings"],
        AuditStage.RISK_DETECTION: ["risk_findings_count"],
        AuditStage.WORKING_PAPERS_GENERATED: ["working_paper_count"],
        AuditStage.EVIDENCE_LINKED: ["evidence_links"],
        AuditStage.REVIEW_NOTES: ["review_notes_cleared"],
        AuditStage.COMPLIANCE_REVIEW: ["compliance_signoff"],
        AuditStage.PARTNER_REVIEW: ["partner_approval", "assigned_reviewer"],
        AuditStage.FINAL_REPORT: ["final_report_pdf"],
        AuditStage.AUDIT_COMPLETED: ["archive_signature"],
    }

    @classmethod
    def validate_transition(cls, state: WorkflowState, target_stage: AuditStage) -> bool:
        """
        Validates if transitioning from state.current_stage to target_stage is allowed.
        Prevents skipping required linear audit lifecycle stages.
        """
        current_index = state.current_stage.get_index()
        target_index = target_stage.get_index()

        if target_index < current_index:
            # Reversion/backtracking is allowed for revisions
            return True

        if target_index > current_index + 1:
            raise InvalidStageTransitionError(
                current_stage=state.current_stage.value,
                target_stage=target_stage.value,
                message=f"Cannot skip from stage '{state.current_stage.value}' to '{target_stage.value}'. Must complete intermediate stages sequentially."
            )

        return True

    @classmethod
    def validate_stage_exit(cls, state: WorkflowState, context_data: Dict[str, Any]) -> bool:
        """
        Validates whether current stage requirements are satisfied before advancing.
        """
        prereqs = cls.STAGE_PREREQUISITES.get(state.current_stage, [])
        missing = []

        for key in prereqs:
            val = context_data.get(key)
            if val is None or (isinstance(val, (list, dict, str)) and len(val) == 0) or val == 0:
                missing.append(key)

        if missing:
            raise StageValidationError(
                stage=state.current_stage.value,
                missing_requirements=missing
            )

        return True

    @classmethod
    def check_operation_prerequisite(cls, operation: str, prerequisite_key: str, context_data: Dict[str, Any]) -> None:
        """
        Checks individual operational prerequisites (e.g. AI analysis requires documents).
        """
        val = context_data.get(prerequisite_key)
        if not val or val == 0:
            raise PrerequisiteNotMetError(operation=operation, prerequisite=prerequisite_key)
