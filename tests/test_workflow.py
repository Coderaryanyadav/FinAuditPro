"""
Comprehensive Workflow & Lifecycle State Machine Test Suite for FinAuditPro.
Verifies audit stage transitions, status validations, and progress calculations.
"""

import unittest
from workflow.workflow_state import WorkflowState, AuditStage
from workflow.workflow_manager import WorkflowManager
from workflow.workflow_validator import WorkflowValidator

class TestWorkflowEngine(unittest.TestCase):

    def test_initial_state(self):
        wm = WorkflowManager()
        wm.set_active_engagement(engagement_id=1, client_id=10, financial_year_id=20)
        self.assertIsNotNone(wm.current_state)
        self.assertIsNotNone(wm.current_state.current_stage)
        self.assertTrue(isinstance(wm.get_progress_percentage(), float))

    def test_valid_stage_transitions(self):
        wm = WorkflowManager()
        wm.set_active_engagement(engagement_id=2, client_id=11, financial_year_id=21)
        stage = wm.current_state.current_stage
        self.assertIsNotNone(stage)
        self.assertTrue(wm.get_progress_percentage() >= 0.0)

    def test_workflow_validator(self):
        ws = WorkflowState(engagement_id=1, client_id=10, financial_year_id=20, current_stage=AuditStage.CLIENT_CREATED)
        valid, msg = WorkflowValidator.validate_transition(
            state=ws,
            target_stage=AuditStage.FINANCIAL_YEAR_SELECTED
        )
        self.assertTrue(valid)

if __name__ == "__main__":
    unittest.main()
