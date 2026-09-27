"""Application service orchestrating local AI Copilot capabilities, context building, citations, and human sign-off."""

import contextlib
import json
from typing import Any
from uuid import uuid4

from finauditpro.application.ai.audit_context_builder import AuditContextBuilder
from finauditpro.application.ai.copilot_prompt_engine import CopilotPromptEngine
from finauditpro.application.ai.llm_provider import LLMProvider, ProviderStatus
from finauditpro.application.ai_dtos import (
    AICopilotDecisionDTO,
    AICopilotRequestDTO,
)
from finauditpro.domain.ai_entities import (
    AICitation,
    AICopilotContext,
    AICopilotResponse,
    AICopilotTaskTypeEnum,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.ai.faiss_vector_store import FAISSVectorStore
from finauditpro.infrastructure.persistence.ai_models import AIRunModel
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    DocumentRepository,
    EngagementRepository,
)


class AICopilotService:
    """Service managing local AI Copilot contextual execution, citations, and explicit auditor confirmation."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        provider: LLMProvider | None = None,
        vector_store: FAISSVectorStore | None = None,
    ) -> None:
        self.db_manager = db_manager
        if provider is None:
            from finauditpro.infrastructure.ai.lmstudio_provider import LMStudioProvider
            provider = LMStudioProvider()
        if vector_store is None:
            from finauditpro.infrastructure.ai.faiss_vector_store import FAISSVectorStore
            from finauditpro.infrastructure.first_run import get_app_data_dir
            vector_store = FAISSVectorStore(get_app_data_dir() / "vector_store")

        self.provider = provider
        self.vector_store = vector_store
        self.context_builder = AuditContextBuilder(db_manager)

    def get_status(self) -> ProviderStatus:
        return self.provider.available()

    def execute_copilot_task(self, dto: AICopilotRequestDTO) -> AICopilotResponse:
        """Execute Copilot task with full context gathering, citation extraction, and audit trail."""
        # 1. Build rich context
        context = self.context_builder.build_context(
            engagement_id=dto.engagement_id,
            audit_area=dto.audit_area,
            target_wp_id=dto.target_object_id if dto.task_type == AICopilotTaskTypeEnum.SUMMARIZE_WORKING_PAPERS else None,
        )

        # 2. Retrieve relevant evidence chunks
        search_query = dto.prompt or dto.task_type.value
        retrieved_chunks = self._retrieve_evidence_chunks(dto.engagement_id, search_query)

        # 3. Build grounded prompt
        messages = CopilotPromptEngine.build_copilot_prompt(
            task_type=dto.task_type,
            user_prompt=dto.prompt,
            context=context,
            retrieved_evidence=retrieved_chunks,
        )

        # 4. Invoke local LLM with offline fallback
        model_id = getattr(self.provider, "chat_model_id", "local-lmstudio")
        try:
            llm_res = self.provider.chat(messages)
            raw_content = llm_res.content
            reasoning = llm_res.reasoning_text or ""
        except Exception:
            # Deterministic Offline Rule-Based Synthesis (Offline resilience)
            offline_synthesis = self._synthesize_offline_response(dto.task_type, dto.prompt, context, retrieved_chunks)
            raw_content = offline_synthesis
            reasoning = "Offline Rule Engine: Generated deterministic response from active audit context (Local LM Studio unavailable)."

        # 5. Extract citations
        citations = CopilotPromptEngine.extract_citations(raw_content, context, retrieved_chunks)

        # 6. Ensure visible AI-generated marker
        run_id = str(uuid4())
        marker = "[AI-GENERATED CONTENT — FOR AUDITOR REVIEW ONLY — REQUIRES PROFESSIONAL SIGN-OFF]"
        final_content = f"{marker}\n\n{raw_content}" if not raw_content.startswith("[AI-GENERATED") else raw_content

        response = AICopilotResponse(
            run_id=run_id,
            task_type=dto.task_type,
            is_ai_generated=True,
            visual_marker=marker,
            content=final_content,
            reasoning_summary=reasoning,
            source_citations=citations,
            suggested_actions=["Review citations", "Accept proposal", "Reject proposal"],
            model_id=model_id,
            model_version="1.0.0",
            user_id=dto.user_id,
            timestamp=utc_now(),
            decision_status="PENDING_REVIEW",
            can_autonomously_modify_audit_record=False,
        )

        # 7. Record run in database
        self._record_copilot_run(dto, response, citations, retrieved_chunks)
        return response

    def accept_copilot_proposal(self, dto: AICopilotDecisionDTO) -> None:
        """Explicitly record human auditor acceptance of an AI-generated proposal."""
        with self.db_manager.session_scope() as session:
            run = session.get(AIRunModel, dto.run_id)
            if not run:
                raise EntityNotFoundError("AI Copilot Run", dto.run_id)
            run.status = "Accepted"
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=run.engagement_id,
                    actor=dto.user_id,
                    action="AI Copilot Proposal Accepted",
                    details=f"Auditor accepted AI Copilot output for run '{run.id[:8]}...'. Notes: {dto.decision_notes or 'None'}",
                )
            )

    def reject_copilot_proposal(self, dto: AICopilotDecisionDTO) -> None:
        """Explicitly record human auditor rejection of an AI-generated proposal."""
        with self.db_manager.session_scope() as session:
            run = session.get(AIRunModel, dto.run_id)
            if not run:
                raise EntityNotFoundError("AI Copilot Run", dto.run_id)
            run.status = "Rejected"
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=run.engagement_id,
                    actor=dto.user_id,
                    action="AI Copilot Proposal Rejected",
                    details=f"Auditor rejected AI Copilot output for run '{run.id[:8]}...'. Reason: {dto.decision_notes or 'Unspecified'}",
                )
            )

    def summarize_evidence(self, engagement_id: str, evidence_id_or_title: str, user_id: str = "Auditor") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.SUMMARIZE_EVIDENCE,
            prompt=f"Summarize key audit evidence for {evidence_id_or_title}",
            target_object_id=evidence_id_or_title,
            user_id=user_id,
        ))

    def explain_exception(self, engagement_id: str, exception_details: str, user_id: str = "Auditor") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.EXPLAIN_EXCEPTIONS,
            prompt=f"Explain deterministic root cause for exception: {exception_details}",
            user_id=user_id,
        ))

    def summarize_working_paper(self, engagement_id: str, wp_id: str, user_id: str = "Auditor") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.SUMMARIZE_WORKING_PAPERS,
            prompt=f"Summarize audit working paper {wp_id}",
            target_object_id=wp_id,
            user_id=user_id,
        ))

    def draft_review_notes(self, engagement_id: str, wp_id: str, user_id: str = "Manager") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.DRAFT_REVIEW_NOTES,
            prompt=f"Draft manager review notes for working paper {wp_id}",
            target_object_id=wp_id,
            user_id=user_id,
        ))

    def suggest_follow_up_questions(self, engagement_id: str, audit_area: str, user_id: str = "Auditor") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.SUGGEST_FOLLOW_UP_QUESTIONS,
            prompt=f"Suggest follow-up management inquiry and PBC questions for {audit_area}",
            audit_area=audit_area,
            user_id=user_id,
        ))

    def explain_financial_anomalies(self, engagement_id: str, anomaly_text: str, user_id: str = "Auditor") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.EXPLAIN_FINANCIAL_ANOMALIES,
            prompt=f"Explain potential drivers of financial anomaly: {anomaly_text}",
            user_id=user_id,
        ))

    def search_engagement_documents(self, engagement_id: str, query: str, user_id: str = "Auditor") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.SEARCH_ENGAGEMENT_DOCUMENTS,
            prompt=f"Search engagement documents for: {query}",
            user_id=user_id,
        ))

    def suggest_relevant_procedures(self, engagement_id: str, area_or_risk: str, user_id: str = "Auditor") -> AICopilotResponse:
        return self.execute_copilot_task(AICopilotRequestDTO(
            engagement_id=engagement_id,
            task_type=AICopilotTaskTypeEnum.SUGGEST_RELEVANT_PROCEDURES,
            prompt=f"Suggest SA 315 / SA 330 audit procedures for {area_or_risk}",
            audit_area=area_or_risk,
            user_id=user_id,
        ))

    def _retrieve_evidence_chunks(self, engagement_id: str, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        with self.db_manager.session_scope() as session:
            doc_repo = DocumentRepository(session)
            page_results = doc_repo.search_pages(engagement_id, query)
            chunks: list[dict[str, Any]] = []
            for doc, page in page_results[:top_k]:
                chunks.append({
                    "chunk_id": f"fts_{page.id}",
                    "document_id": doc.id,
                    "title": doc.filename,
                    "page_number": page.page_number,
                    "chunk_text": page.extracted_text or "",
                    "score": 1.0,
                })
            return chunks

    def _synthesize_offline_response(
        self,
        task_type: AICopilotTaskTypeEnum,
        prompt: str,
        context: AICopilotContext,
        chunks: list[dict[str, Any]],
    ) -> str:
        """Deterministic rule-based synthesis when local LLM server is disconnected."""
        lines = [f"**Copilot Advisory Output ({task_type.value}):**"]

        if task_type == AICopilotTaskTypeEnum.SUMMARIZE_WORKING_PAPERS:
            wp = context.active_working_papers[0] if context.active_working_papers else {"index_reference": "WP-001", "title": "Audit Schedule", "status": "DRAFT"}
            lines.append(f"• Working Paper: [{wp['index_reference']}] - {wp['title']}")
            lines.append(f"• Status: {wp.get('status', 'DRAFT')}")
            lines.append(f"• Linked Procedures: {len(context.active_procedures)} active procedure(s)")
            lines.append(f"• Open Findings: {len(context.active_findings)} finding(s)")
            lines.append("• Conclusion: Pending reviewer clearance and sign-off.")
        elif task_type == AICopilotTaskTypeEnum.EXPLAIN_EXCEPTIONS:
            exc = context.active_exceptions[0] if context.active_exceptions else {"exception_id": "EXC-001", "title": "Sample Discrepancy", "evidence": "Amount variance"}
            lines.append(f"• Exception Reference: [{exc['exception_id']}] {exc['title']}")
            lines.append(f"• Computed Evidence: {exc['evidence']}")
            lines.append("• Accounting Standard: Requires verification under SA 500 / Schedule III.")
        elif task_type == AICopilotTaskTypeEnum.DRAFT_REVIEW_NOTES:
            lines.append("• Proposed Review Note 1: Verify third-party confirmation response tie-back [SA 505].")
            lines.append("• Proposed Review Note 2: Confirm sample size calculation conforms to SA 320 performance materiality.")
        else:
            lines.append(f"Grounded Context for Engagement [{context.engagement_title}]:")
            if context.active_risks:
                lines.append(f"• Related Risk: [{context.active_risks[0]['risk_code']}] {context.active_risks[0]['title']}")
            if context.active_procedures:
                lines.append(f"• Related Procedure: [{context.active_procedures[0]['procedure_code']}]")
            if chunks:
                lines.append(f"• Evidence Source: [{chunks[0]['chunk_id']}] in {chunks[0]['title']}")

        return "\n".join(lines)

    def _record_copilot_run(
        self,
        dto: AICopilotRequestDTO,
        response: AICopilotResponse,
        citations: list[AICitation],
        retrieved_chunks: list[dict[str, Any]],
    ) -> None:
        with contextlib.suppress(Exception), self.db_manager.session_scope() as session:
            run_model = AIRunModel(
                id=response.run_id,
                engagement_id=dto.engagement_id,
                run_kind=dto.task_type.value,
                model_id=response.model_id,
                parameters_json=json.dumps({"temperature": 0.6, "task": dto.task_type.value}),
                prompt_version=CopilotPromptEngine.COPILOT_PROMPT_VERSION,
                retrieved_chunk_ids_json=json.dumps([c["chunk_id"] for c in retrieved_chunks]),
                reasoning_text=response.reasoning_summary,
                response_text=response.content,
                status="Completed",
                created_by=dto.user_id,
            )
            session.add(run_model)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.user_id,
                    action=f"AI Copilot Executed: {dto.task_type.value}",
                    details=f"Generated {len(citations)} citations. Model: {response.model_id}.",
                )
            )
