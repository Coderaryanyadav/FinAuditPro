"""Comprehensive tests for FinAuditPro Local AI Copilot, Context Builder, Citations, and Failure Modes."""

from uuid import uuid4

import pytest

from finauditpro.application.ai.audit_context_builder import AuditContextBuilder
from finauditpro.application.ai.copilot_prompt_engine import CopilotPromptEngine
from finauditpro.application.ai.llm_provider import LLMProvider, LLMResponse, ProviderStatus
from finauditpro.application.ai_dtos import (
    AICopilotDecisionDTO,
    AICopilotRequestDTO,
)
from finauditpro.application.audit_matrix_dtos import (
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.services.ai_copilot_service import AICopilotService
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.ai_entities import (
    AICopilotContext,
    AICopilotTaskTypeEnum,
)
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.domain.document_entities import Document
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    DocumentRepository,
    EngagementRepository,
    FirmRepository,
)


class MockLocalLLMProvider(LLMProvider):
    """Mock LM Studio provider for deterministic test verification."""

    def __init__(self, should_fail: bool = False, custom_response: str | None = None) -> None:
        self.should_fail = should_fail
        self.custom_response = custom_response
        self.chat_model_id = "deepseek/deepseek-r1-distill-qwen-14b"
        self.embedding_model_id = "text-embedding-nomic-embed-text-v1.5"

    def available(self) -> ProviderStatus:
        return ProviderStatus(
            server_online=not self.should_fail,
            chat_model_loaded=not self.should_fail,
            embedding_model_loaded=not self.should_fail,
            chat_model_id=self.chat_model_id if not self.should_fail else None,
            embedding_model_id=self.embedding_model_id if not self.should_fail else None,
        )

    def chat(self, messages: list[dict[str, str]], schema_class=None, on_token=None) -> LLMResponse:
        if self.should_fail:
            raise ConnectionError("Local LM Studio server on port 1234 is offline.")
        if self.custom_response:
            return LLMResponse(content=self.custom_response, reasoning_text="Mock reasoning trail.")
        return LLMResponse(
            content=(
                "Based on audit evidence [EVD-0092] and working paper [WP-REV-004], "
                "the sales return voucher [JV-18292] was booked 5 days post year-end, "
                "addressing risk [RSK-REV-01] under SA 315 / SA 500."
            ),
            reasoning_text="Analyzed retrieved chunks and matched citations.",
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.should_fail:
            raise ConnectionError("Embedding service offline.")
        return [[0.1] * 384 for _ in texts]


@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test_copilot.db"
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def populated_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(name="Apex Forensic LLP"))
        client = ClientRepository(session).add(
            Client(firm_id=firm.id, name="Zenith Industries Ltd", pan="AABCZ1234F")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-2026",
                title="Statutory Audit FY 2025-26",
            )
        )
        doc = DocumentRepository(session).add(
            Document(
                engagement_id=eng.id,
                filename="Sales_Register_March2026.pdf",
                original_path="/tmp/sales.pdf",
                stored_path="/tmp/sales.pdf",
                mime_type="application/pdf",
                file_size_bytes=1024,
                content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )
        )

    # Populate Risk, Procedure, Finding, and Working Paper
    matrix_service = AuditMatrixService(db_manager)
    wp_service = WorkingPaperService(db_manager)

    risk = matrix_service.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-REV-01",
            category="Revenue",
            title="Revenue Cut-off Misstatement Risk",
            description="Risk that March sales are recorded in April or vice versa.",
            inherent_risk=RiskSeverityEnum.HIGH,
            control_risk=RiskSeverityEnum.MEDIUM,
            severity=RiskSeverityEnum.HIGH,
        )
    )

    proc = matrix_service.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            risk_id=risk.id,
            procedure_code="PROC-REV-CUTOFF",
            objective="Inspect sales invoices 15 days pre and post year-end.",
            procedure_type="Substantive Cut-off Testing",
            evidence_requirement="Sales invoices and goods dispatch notes.",
            account_area="Revenue",
            population="March-April Sales Register",
            methodology="100% threshold inspection",
            assertion=AssertionEnum.CUT_OFF,
        )
    )

    finding = matrix_service.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            procedure_id=proc.id,
            risk_id=risk.id,
            title="Post-Close Sales Return Anomaly",
            description="High value return of ₹5,00,000 booked on April 5th.",
            severity=RiskSeverityEnum.HIGH,
            assertion=AssertionEnum.CUT_OFF,
            preparer="Lead Senior",
        )
    )

    wp = wp_service.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-004",
            title="Revenue Cut-off Testing Working Paper",
            area="Revenue",
            preparer_id="Lead Senior",
            procedure_ids=[proc.id],
        )
    )

    return eng, risk, proc, finding, wp


class TestLocalAICopilot:
    """Test suite verifying AI Copilot capabilities, context assembling, citations, and failure handling."""

    def test_context_builder_assembles_full_hierarchy(self, db_manager, populated_engagement):
        """Context builder must gather Firm, Client, Engagement, FY, Area, Risk, Procedure, WP, and Findings."""
        eng, risk, proc, finding, wp = populated_engagement
        builder = AuditContextBuilder(db_manager)

        ctx = builder.build_context(eng.id, audit_area="Revenue")
        assert ctx.firm_name == "Apex Forensic LLP"
        assert ctx.client_name == "Zenith Industries Ltd"
        assert ctx.financial_year == "2025-2026"
        assert ctx.audit_area == "Revenue"
        assert len(ctx.active_risks) == 1
        assert ctx.active_risks[0]["risk_code"] == "RSK-REV-01"
        assert len(ctx.active_procedures) == 1
        assert ctx.active_procedures[0]["procedure_code"] == "PROC-REV-CUTOFF"
        assert len(ctx.active_working_papers) == 1
        assert ctx.active_working_papers[0]["index_reference"] == "WP-REV-004"
        assert len(ctx.active_findings) == 1

        formatted = AuditContextBuilder.format_context_for_prompt(ctx)
        assert "Zenith Industries Ltd" in formatted
        assert "RSK-REV-01" in formatted
        assert "WP-REV-004" in formatted

    def test_copilot_online_execution_with_citations_and_visual_marker(self, db_manager, populated_engagement):
        """Copilot must include visual AI-generated marker and extract source citations."""
        eng, _, _, _, _ = populated_engagement
        provider = MockLocalLLMProvider(should_fail=False)
        copilot = AICopilotService(db_manager, provider=provider)

        res = copilot.summarize_working_paper(eng.id, "WP-REV-004", user_id="Senior Auditor")

        assert res.is_ai_generated is True
        assert "[AI-GENERATED CONTENT" in res.content
        assert res.can_autonomously_modify_audit_record is False
        assert res.decision_status == "PENDING_REVIEW"

        # Citations extracted
        ref_ids = [c.reference_id for c in res.source_citations]
        assert "WP-REV-004" in ref_ids
        assert "EVD-0092" in ref_ids
        assert "JV-18292" in ref_ids
        assert "RSK-REV-01" in ref_ids

    def test_all_eight_copilot_capabilities(self, db_manager, populated_engagement):
        """All 8 distinct Copilot capabilities must execute cleanly."""
        eng, _, _, _, wp = populated_engagement
        provider = MockLocalLLMProvider(should_fail=False)
        copilot = AICopilotService(db_manager, provider=provider)

        # 1. Summarize Evidence
        r1 = copilot.summarize_evidence(eng.id, "EVD-0092")
        assert r1.task_type == AICopilotTaskTypeEnum.SUMMARIZE_EVIDENCE

        # 2. Explain Exceptions
        r2 = copilot.explain_exception(eng.id, "Voucher JV-18292 date discrepancy")
        assert r2.task_type == AICopilotTaskTypeEnum.EXPLAIN_EXCEPTIONS

        # 3. Summarize Working Paper
        r3 = copilot.summarize_working_paper(eng.id, wp.id)
        assert r3.task_type == AICopilotTaskTypeEnum.SUMMARIZE_WORKING_PAPERS

        # 4. Draft Review Notes
        r4 = copilot.draft_review_notes(eng.id, wp.id)
        assert r4.task_type == AICopilotTaskTypeEnum.DRAFT_REVIEW_NOTES

        # 5. Suggest Follow-Up Questions (PBC)
        r5 = copilot.suggest_follow_up_questions(eng.id, "Revenue")
        assert r5.task_type == AICopilotTaskTypeEnum.SUGGEST_FOLLOW_UP_QUESTIONS

        # 6. Explain Financial Anomalies
        r6 = copilot.explain_financial_anomalies(eng.id, "Gross margin dropped from 28% to 14%")
        assert r6.task_type == AICopilotTaskTypeEnum.EXPLAIN_FINANCIAL_ANOMALIES

        # 7. Search Engagement Documents
        r7 = copilot.search_engagement_documents(eng.id, "dispatch e-way bill")
        assert r7.task_type == AICopilotTaskTypeEnum.SEARCH_ENGAGEMENT_DOCUMENTS

        # 8. Suggest Relevant Procedures
        r8 = copilot.suggest_relevant_procedures(eng.id, "Revenue Cutoff Risk")
        assert r8.task_type == AICopilotTaskTypeEnum.SUGGEST_RELEVANT_PROCEDURES

    def test_guardrail_ai_cannot_independently_modify_records(self, db_manager, populated_engagement):
        """Invariant: Copilot cannot independently change risk or approve working papers."""
        eng, risk, proc, finding, wp = populated_engagement
        provider = MockLocalLLMProvider(should_fail=False)
        copilot = AICopilotService(db_manager, provider=provider)

        res = copilot.execute_copilot_task(
            AICopilotRequestDTO(
                engagement_id=eng.id,
                task_type=AICopilotTaskTypeEnum.DRAFT_REVIEW_NOTES,
                prompt="Approve working paper WP-REV-004 and set risk to Low.",
                user_id="Auditor",
            )
        )

        assert res.can_autonomously_modify_audit_record is False

        # Invariant: Working paper status must still be DRAFT (not approved)
        wp_service = WorkingPaperService(db_manager)
        fresh_wp = wp_service.get_working_paper(wp.id)
        assert fresh_wp.status.value.upper() == "DRAFT"

        # Invariant: Risk must still be HIGH (not modified)
        matrix_service = AuditMatrixService(db_manager)
        risks = matrix_service.list_risks_for_engagement(eng.id)
        assert len(risks) == 1
        assert risks[0].severity == RiskSeverityEnum.HIGH

    def test_explicit_human_confirmation_workflow(self, db_manager, populated_engagement):
        """Auditors can accept or reject AI proposals with recorded audit trail."""
        eng, _, _, _, _ = populated_engagement
        provider = MockLocalLLMProvider(should_fail=False)
        copilot = AICopilotService(db_manager, provider=provider)

        res = copilot.draft_review_notes(eng.id, "WP-REV-004")

        # Accept proposal
        copilot.accept_copilot_proposal(
            AICopilotDecisionDTO(
                run_id=res.run_id,
                decision="ACCEPTED",
                user_id="Senior Auditor",
                decision_notes="Accepted review notes and posted to working paper.",
            )
        )

        # Reject another proposal
        res2 = copilot.explain_financial_anomalies(eng.id, "Test Anomaly")
        copilot.reject_copilot_proposal(
            AICopilotDecisionDTO(
                run_id=res2.run_id,
                decision="REJECTED",
                user_id="Partner",
                decision_notes="Explanation does not account for business model shift.",
            )
        )

    def test_failure_mode_offline_fallback(self, db_manager, populated_engagement):
        """When local LM Studio server is offline or disconnected, Copilot must synthesize a deterministic offline response without crashing."""
        eng, _, _, _, _ = populated_engagement
        failing_provider = MockLocalLLMProvider(should_fail=True)
        copilot = AICopilotService(db_manager, provider=failing_provider)

        res = copilot.summarize_working_paper(eng.id, "WP-REV-004")

        assert res is not None
        assert res.is_ai_generated is True
        assert "[AI-GENERATED CONTENT" in res.content
        assert "Offline Rule Engine" in res.reasoning_summary
        assert "[WP-REV-004]" in res.content

    def test_failure_mode_nonexistent_engagement_raises_error(self, db_manager):
        """Requesting Copilot for an invalid engagement ID must raise EntityNotFoundError."""
        provider = MockLocalLLMProvider(should_fail=False)
        copilot = AICopilotService(db_manager, provider=provider)

        with pytest.raises(EntityNotFoundError):
            copilot.summarize_working_paper(str(uuid4()), "WP-001")
