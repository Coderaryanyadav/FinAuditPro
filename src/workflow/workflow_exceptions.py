"""
Workflow Custom Exceptions for FinAuditPro.
Provides granular domain exception types for audit lifecycle state transitions and validation rules.
"""

from core.exceptions import FinAuditError

class WorkflowError(FinAuditError):
    """Base exception for all workflow engine errors."""
    pass

class InvalidStageTransitionError(WorkflowError):
    """Raised when attempting an illegal transition between audit stages (e.g. Stage 2 -> Stage 10)."""
    def __init__(self, current_stage: str, target_stage: str, message: str = None):
        self.current_stage = current_stage
        self.target_stage = target_stage
        msg = message or f"Cannot transition audit engagement from stage '{current_stage}' directly to '{target_stage}'."
        super().__init__(msg)

class StageValidationError(WorkflowError):
    """Raised when stage exit prerequisites or completion criteria fail validation."""
    def __init__(self, stage: str, missing_requirements: list, message: str = None):
        self.stage = stage
        self.missing_requirements = missing_requirements
        msg = message or f"Validation failed for stage '{stage}'. Missing requirements: {', '.join(missing_requirements)}"
        super().__init__(msg)

class PrerequisiteNotMetError(WorkflowError):
    """Raised when attempting an operation without its prerequisite data (e.g. Findings before OCR)."""
    def __init__(self, operation: str, prerequisite: str):
        self.operation = operation
        self.prerequisite = prerequisite
        msg = f"Cannot perform '{operation}' because prerequisite '{prerequisite}' is missing."
        super().__init__(msg)

class WorkflowStateCorruptedError(WorkflowError):
    """Raised when cached/persisted workflow state is invalid or unrecoverable."""
    pass
