"""Application service for Guided Audit Engagement Workflow evaluation and factual status tracking."""

from dataclasses import dataclass, field
from typing import Any

from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import (
    ClientModel,
    EngagementModel,
    FirmModel,
)


@dataclass
class WorkflowStepDTO:
    step_key: str
    title: str
    is_completed: bool
    incomplete_reason: str | None = None
    target_route: str = ""


@dataclass
class WorkflowStageDTO:
    stage_number: int
    stage_key: str
    title: str
    description: str
    steps: list[WorkflowStepDTO] = field(default_factory=list)
    completion_percentage: float = 0.0
    status: str = "Not Started"
    incomplete_reasons: list[str] = field(default_factory=list)


@dataclass
class EngagementWorkflowDTO:
    engagement_id: str
    firm_name: str
    client_name: str
    financial_year: str
    engagement_title: str
    audit_type: str
    stages: list[WorkflowStageDTO] = field(default_factory=list)
    overall_progress: float = 0.0


class GuidedWorkflowService:
    """Service evaluating engagement progress against factual database records without fabrication."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def evaluate_workflow(self, engagement_id: str) -> EngagementWorkflowDTO:
        with self.db_manager.session_scope() as session:
            eng = session.query(EngagementModel).filter(EngagementModel.id == engagement_id).first()
            if not eng:
                return EngagementWorkflowDTO(
                    engagement_id=engagement_id,
                    firm_name="N/A",
                    client_name="N/A",
                    financial_year="N/A",
                    engagement_title="No Active Engagement",
                    audit_type="Statutory Audit",
                )

            firm = session.query(FirmModel).filter(FirmModel.id == eng.firm_id).first()
            client = session.query(ClientModel).filter(ClientModel.id == eng.client_id).first()

            firm_name = firm.name if firm else "Practice Firm"
            client_name = client.name if client else "Client Entity"
            fy = eng.financial_year
            audit_type = getattr(eng, "audit_type", "Statutory Audit")

            stages = [
                self._evaluate_stage_1(session, engagement_id),
                self._evaluate_stage_2(session, engagement_id),
                self._evaluate_stage_3(session, engagement_id),
                self._evaluate_stage_4(session, engagement_id),
            ]
            total_steps = sum(len(st.steps) for st in stages)
            completed_steps = sum(sum(1 for s in st.steps if s.is_completed) for st in stages)
            overall_progress = round((completed_steps / total_steps * 100.0), 1) if total_steps > 0 else 0.0

            return EngagementWorkflowDTO(
                engagement_id=engagement_id,
                firm_name=firm_name,
                client_name=client_name,
                financial_year=fy,
                engagement_title=f"{client_name} — {audit_type} ({fy})",
                audit_type=audit_type,
                stages=stages,
                overall_progress=overall_progress,
            )

    def _evaluate_stage_1(self, session: Any, engagement_id: str) -> WorkflowStageDTO:
        steps = [
            WorkflowStepDTO("engagement_setup", "Engagement Details & Entity Setup", True, target_route="engagements")
        ]

        mat_count = 0
        try:
            from finauditpro.infrastructure.persistence.models import MaterialityAssessmentModel

            mat_count = session.query(MaterialityAssessmentModel).filter(MaterialityAssessmentModel.engagement_id == engagement_id).count()
        except Exception:
            mat_count = 0

        mat_completed = mat_count > 0
        steps.append(WorkflowStepDTO("materiality", "Materiality Benchmark & Thresholds", mat_completed, None if mat_completed else "Materiality not finalized", "audit_matrix"))

        risk_count = 0
        try:
            from finauditpro.infrastructure.persistence.models import AuditRiskModel

            risk_count = session.query(AuditRiskModel).filter(AuditRiskModel.engagement_id == engagement_id).count()
        except Exception:
            risk_count = 0

        risk_completed = risk_count > 0
        steps.append(WorkflowStepDTO("risk_assessment", "Risk Assessment & Audit Matrix", risk_completed, None if risk_completed else "Audit risks not identified", "audit_matrix"))

        proc_count = 0
        try:
            from finauditpro.infrastructure.persistence.models import AuditProcedureModel

            proc_count = session.query(AuditProcedureModel).filter(AuditProcedureModel.engagement_id == engagement_id).count()
        except Exception:
            proc_count = 0

        proc_completed = proc_count > 0
        steps.append(WorkflowStepDTO("audit_planning", "Audit Program & Scope Definition", proc_completed, None if proc_completed else "Audit procedures not scoped", "audit_matrix"))

        return self._build_stage_dto(1, "setup_planning", "Setup & Planning", "Define materiality, assess risks, and scope procedures.", steps)

    def _evaluate_stage_2(self, session: Any, engagement_id: str) -> WorkflowStageDTO:
        tb_count = 0
        try:
            from finauditpro.infrastructure.persistence.models import FinancialDatasetModel

            tb_count = session.query(FinancialDatasetModel).filter(FinancialDatasetModel.engagement_id == engagement_id).count()
        except Exception:
            tb_count = 0

        tb_completed = tb_count > 0
        steps = [
            WorkflowStepDTO("trial_balance", "Trial Balance & General Ledger Scrutiny", tb_completed, None if tb_completed else "Trial balance not imported / imbalanced", "financial_data"),
            WorkflowStepDTO("lead_schedules", "Lead Schedules & Classifications", tb_completed, None if tb_completed else "Lead schedules pending", "financial_data"),
            WorkflowStepDTO("analytics", "Substantive Analytics & Exception Scrutiny", tb_completed, None if tb_completed else "Analytics not executed", "financial_data"),
        ]
        return self._build_stage_dto(2, "financial_data", "Financial Data", "Scrutinize Trial Balance, General Ledger, and analytical exceptions.", steps)

    def _evaluate_stage_3(self, session: Any, engagement_id: str) -> WorkflowStageDTO:
        wp_count = 0
        open_notes_count = 0
        unreviewed_count = 0
        try:
            from finauditpro.infrastructure.persistence.working_paper_models import (
                ReviewNoteModel,
                WorkingPaperModel,
            )

            wps = session.query(WorkingPaperModel).filter(WorkingPaperModel.engagement_id == engagement_id).all()
            wp_count = len(wps)
            wp_ids = [w.id for w in wps]
            if wp_ids:
                open_notes_count = session.query(ReviewNoteModel).filter(
                    ReviewNoteModel.working_paper_id.in_(wp_ids),
                    ReviewNoteModel.status == "Open",
                ).count()
                unreviewed_count = sum(1 for w in wps if str(getattr(w, "status", "")).lower() not in ("approved", "locked"))
        except Exception:
            wp_count = 0
            open_notes_count = 0
            unreviewed_count = 0

        if wp_count == 0:
            steps = [
                WorkflowStepDTO("evidence_linking", "Audit Evidence & Document Attachment", False, "Evidence documents not attached", "documents"),
                WorkflowStepDTO("working_papers", "Working Papers Execution & Conclusion", False, "No working papers generated", "working_papers"),
                WorkflowStepDTO("review_notes", "Maker-Checker & Review Notes Resolution", False, "Review notes pending resolution", "working_papers"),
            ]
        else:
            steps = [
                WorkflowStepDTO("evidence_linking", "Audit Evidence & Document Attachment", True, target_route="documents"),
                WorkflowStepDTO(
                    "working_papers",
                    "Working Papers Execution & Conclusion",
                    unreviewed_count == 0,
                    f"{unreviewed_count} working papers awaiting review" if unreviewed_count > 0 else None,
                    "working_papers",
                ),
                WorkflowStepDTO(
                    "review_notes",
                    "Maker-Checker & Review Notes Resolution",
                    open_notes_count == 0,
                    f"{open_notes_count} open review notes" if open_notes_count > 0 else None,
                    "working_papers",
                ),
            ]
        return self._build_stage_dto(3, "fieldwork_evidence", "Fieldwork & Evidence", "Execute working papers, attach evidence, and resolve review notes.", steps)

    def _evaluate_stage_4(self, session: Any, engagement_id: str) -> WorkflowStageDTO:
        report_count = 0
        try:
            from finauditpro.infrastructure.persistence.report_models import ReportModel

            report_count = session.query(ReportModel).filter(ReportModel.engagement_id == engagement_id).count()
        except Exception:
            report_count = 0

        rep_completed = report_count > 0
        steps = [
            WorkflowStepDTO("statutory_report", "Statutory Audit Report Generation", rep_completed, None if rep_completed else "Report not generated", "reports")
        ]

        signoff_count = 0
        try:
            from finauditpro.infrastructure.persistence.working_paper_models import (
                SignOffRecordModel,
                WorkingPaperModel,
            )

            wp_ids = [w.id for w in session.query(WorkingPaperModel).filter(WorkingPaperModel.engagement_id == engagement_id).all()]
            if wp_ids:
                signoff_count = session.query(SignOffRecordModel).filter(
                    SignOffRecordModel.working_paper_id.in_(wp_ids),
                    SignOffRecordModel.level == "Partner",
                ).count()
        except Exception:
            signoff_count = 0

        sign_completed = signoff_count > 0
        steps.append(WorkflowStepDTO("partner_signoff", "Partner Sign-Off & Audit Seal", sign_completed, None if sign_completed else "Partner sign-off pending", "reports"))

        arch_count = 0
        try:
            from finauditpro.infrastructure.persistence.archival_models import (
                EngagementArchiveModel,
            )

            arch_count = session.query(EngagementArchiveModel).filter(EngagementArchiveModel.engagement_id == engagement_id).count()
        except Exception:
            arch_count = 0

        arch_completed = arch_count > 0
        steps.append(WorkflowStepDTO("archival", "Audit File Archival (SQC 1 / SA 230)", arch_completed, None if arch_completed else "Audit file not archived", "archival"))
        steps.append(WorkflowStepDTO("roll_forward", "Roll-Forward to Next Financial Year", False, "Roll-forward pending finalization", "roll_forward"))

        return self._build_stage_dto(4, "review_reporting", "Review & Reporting", "Finalize statutory audit reports, partner sign-off, and file archival.", steps)

    def _build_stage_dto(
        self, stage_num: int, key: str, title: str, desc: str, steps: list[WorkflowStepDTO]
    ) -> WorkflowStageDTO:
        c_count = sum(1 for s in steps if s.is_completed)
        total = len(steps)
        pct = round((c_count / total * 100.0), 1) if total > 0 else 0.0
        status = "Complete" if pct == 100.0 else ("In Progress" if c_count > 0 else "Not Started")
        reasons = [s.incomplete_reason for s in steps if not s.is_completed and s.incomplete_reason]

        return WorkflowStageDTO(
            stage_number=stage_num,
            stage_key=key,
            title=title,
            description=desc,
            steps=steps,
            completion_percentage=pct,
            status=status,
            incomplete_reasons=reasons,
        )
