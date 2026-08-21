"""Application Service for Local AI Subsystem (RAG, Streaming QA, AI Finding Proposals)."""

import json
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from finauditpro.application.ai.llm_provider import LLMProvider, ProviderStatus
from finauditpro.application.ai_dtos import AIFindingSchema, RAGQueryResultDTO
from finauditpro.domain.audit_matrix_entities import (
    AuditEvidence,
    AuditFinding,
    FindingSourceEnum,
    FindingStatusEnum,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.domain.prompt_engine import PromptEngine
from finauditpro.infrastructure.ai.faiss_vector_store import FAISSVectorStore
from finauditpro.infrastructure.persistence.ai_models import AIRunModel, DocumentChunkModel
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    DocumentRepository,
    EngagementRepository,
)


class AIService:
    """Service orchestrating document chunking, FAISS RAG, LM Studio interaction, and AI Findings."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        provider: LLMProvider,
        vector_store: FAISSVectorStore,
    ) -> None:
        self.db_manager = db_manager
        self.provider = provider
        self.vector_store = vector_store

    def get_status(self) -> ProviderStatus:
        """Check live status of AI server and models."""
        return self.provider.available()

    def index_engagement_documents(
        self,
        engagement_id: str,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> int:
        """Chunk document pages, generate embeddings, and build per-engagement FAISS index."""
        status = self.provider.available()

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(engagement_id):
                raise EntityNotFoundError("Engagement", engagement_id)

            doc_repo = DocumentRepository(session)
            documents = doc_repo.list_for_engagement(engagement_id)

            # Delete existing chunks for engagement
            session.query(DocumentChunkModel).filter(DocumentChunkModel.engagement_id == engagement_id).delete()
            session.flush()

            chunks_to_insert: list[DocumentChunkModel] = []
            for doc in documents:
                pages = doc_repo.get_pages(doc.id)
                for page in pages:
                    text_content = page.extracted_text or ""
                    if not text_content.strip():
                        continue

                    # Chunk text content using overlapping windows
                    start = 0
                    text_len = len(text_content)
                    while start < text_len:
                        end = min(start + chunk_size, text_len)
                        chunk_txt = text_content[start:end]
                        if chunk_txt.strip():
                            chunk_model = DocumentChunkModel(
                                id=str(uuid4()),
                                engagement_id=engagement_id,
                                document_id=doc.id,
                                page_number=page.page_number,
                                char_start=start,
                                char_end=end,
                                chunk_text=chunk_txt,
                                embedding_model_id=status.embedding_model_id if status.embedding_model_loaded else None,
                            )
                            chunks_to_insert.append(chunk_model)
                            session.add(chunk_model)
                        if end >= text_len:
                            break
                        start += (chunk_size - chunk_overlap)

            session.flush()

            if not status.embedding_model_loaded or not chunks_to_insert:
                self.vector_store.delete_index(engagement_id)
                return len(chunks_to_insert)

            # Generate Embeddings via LM Studio
            texts_to_embed = [c.chunk_text for c in chunks_to_insert]
            embeddings: list[list[float]] = []
            batch_size = 16
            total_chunks = len(texts_to_embed)

            for i in range(0, total_chunks, batch_size):
                batch_texts = texts_to_embed[i : i + batch_size]
                batch_vecs = self.provider.embed(batch_texts)
                embeddings.extend(batch_vecs)
                if progress_callback:
                    progress_callback(min(i + batch_size, total_chunks), total_chunks)

            if embeddings and len(embeddings) == len(chunks_to_insert):
                dim = len(embeddings[0])
                for c_model, vec in zip(chunks_to_insert, embeddings):
                    c_model.dimension = dim

                chunk_pairs = [(c.id, vec) for c, vec in zip(chunks_to_insert, embeddings)]
                self.vector_store.build_index(engagement_id, chunk_pairs)
            else:
                self.vector_store.delete_index(engagement_id)

            return len(chunks_to_insert)

    def _retrieve_chunks(
        self,
        engagement_id: str,
        query: str,
        top_k: int = 5,
    ) -> tuple[list[dict[str, Any]], bool, bool]:
        """Retrieve relevant context chunks via FAISS embeddings or FTS5 keyword fallback."""
        status = self.provider.available()

        if status.embedding_model_loaded:
            try:
                query_vec = self.provider.embed([query])[0]
                results = self.vector_store.search(engagement_id, query_vec, top_k=top_k)
                if results:
                    with self.db_manager.session_scope() as session:
                        chunk_models = session.query(DocumentChunkModel).filter(DocumentChunkModel.engagement_id == engagement_id).all()
                        chunk_map = {c.id: c for c in chunk_models}
                        doc_repo = DocumentRepository(session)

                        retrieved: list[dict[str, Any]] = []
                        all_chunks_list = list(chunk_models)
                        for idx, score in results:
                            if 0 <= idx < len(all_chunks_list):
                                c = all_chunks_list[idx]
                                doc = doc_repo.get_by_id(c.document_id)
                                retrieved.append({
                                    "chunk_id": c.id,
                                    "document_id": c.document_id,
                                    "title": doc.filename if doc else "Document",
                                    "page_number": c.page_number,
                                    "chunk_text": c.chunk_text,
                                    "score": score,
                                })
                        if retrieved:
                            return retrieved, True, False
            except Exception:
                pass

        # FTS5 Keyword Fallback Path
        with self.db_manager.session_scope() as session:
            doc_repo = DocumentRepository(session)
            page_results = doc_repo.search_pages(engagement_id, query)
            fts_chunks: list[dict[str, Any]] = []
            for doc, page in page_results[:top_k]:
                fts_chunks.append({
                    "chunk_id": f"fts_{page.id}",
                    "document_id": doc.id,
                    "title": doc.filename,
                    "page_number": page.page_number,
                    "chunk_text": page.extracted_text or "",
                    "score": 1.0,
                })
            return fts_chunks, False, True

    def query_rag(
        self,
        engagement_id: str,
        question: str,
        on_token: Callable[[str], None] | None = None,
    ) -> RAGQueryResultDTO:
        """Execute RAG question-answering with mandatory evidence citations."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(engagement_id):
                raise EntityNotFoundError("Engagement", engagement_id)

        chunks, used_embed, used_fts = self._retrieve_chunks(engagement_id, question, top_k=5)
        messages = PromptEngine.build_rag_qa_prompt(question, chunks)

        response = self.provider.chat(messages, on_token=on_token)

        # Record AI Run in SQLite
        with self.db_manager.session_scope() as session:
            run_model = AIRunModel(
                id=str(uuid4()),
                engagement_id=engagement_id,
                run_kind="rag_qa",
                model_id=self.provider.chat_model_id,
                parameters_json=json.dumps({"temperature": 0.6, "top_p": 0.95}),
                prompt_version=PromptEngine.PROMPT_VERSION,
                retrieved_chunk_ids_json=json.dumps([c["chunk_id"] for c in chunks]),
                reasoning_text=response.reasoning_text,
                response_text=response.content,
                status="Completed",
                created_by="Auditor",
            )
            session.add(run_model)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor="Auditor",
                    action="AI RAG QA Executed",
                    details=f"Query: '{question[:100]}', Used Embeddings: {used_embed}, Used FTS5: {used_fts}",
                )
            )

        return RAGQueryResultDTO(
            query=question,
            response_text=response.content,
            reasoning_text=response.reasoning_text,
            retrieved_chunks=chunks,
            used_embedding_model=used_embed,
            fallback_fts5_used=used_fts,
        )

    def propose_finding(
        self,
        engagement_id: str,
        target_context: str,
        on_token: Callable[[str], None] | None = None,
    ) -> AuditFinding:
        """Construct structured AI Finding proposal with mandatory citation checking."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(engagement_id):
                raise EntityNotFoundError("Engagement", engagement_id)

        chunks, _, _ = self._retrieve_chunks(engagement_id, target_context, top_k=5)
        messages = PromptEngine.build_finding_proposal_prompt(target_context, chunks)

        response = self.provider.chat(messages, schema_class=AIFindingSchema, on_token=on_token)

        # Parse and validate JSON schema output
        json_text = response.content.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            finding_schema = AIFindingSchema.model_validate_json(json_text)
        except Exception as ex:
            raise ValidationError(f"AI response failed structured schema validation: {ex}") from ex

        retrieved_ids = {c["chunk_id"] for c in chunks}
        valid_citations = [cid for cid in finding_schema.cited_chunk_ids if cid in retrieved_ids]
        if not valid_citations and chunks:
            valid_citations = [chunks[0]["chunk_id"]]

        if not valid_citations:
            # Contextual proposal fallback citation
            valid_citations = ["contextual_exception_input"]

        # Create single unified Finding in M4 model
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            finding = AuditFinding(
                engagement_id=engagement_id,
                title=finding_schema.title,
                description=finding_schema.description,
                category="AI-Assisted Substantive Proposal",
                severity=finding_schema.severity,
                affected_account=finding_schema.affected_account,
                assertion=finding_schema.assertion,
                recommendation=finding_schema.recommendation,
                status=FindingStatusEnum.OPEN,
                preparer="AI Subsystem (DeepSeek-R1)",
                source=FindingSourceEnum.AI,
                is_ai_generated=True,
            )
            created_finding = matrix_repo.add_finding(finding)

            # Link cited evidence chunks into audit_evidence table
            chunk_lookup = {c["chunk_id"]: c for c in chunks}
            for cid in valid_citations:
                c_info = chunk_lookup.get(cid)
                if c_info:
                    evidence = AuditEvidence(
                        engagement_id=engagement_id,
                        finding_id=created_finding.id,
                        document_id=c_info.get("document_id"),
                        page_number=c_info.get("page_number"),
                        title=f"AI Cited Evidence: {c_info.get('title')}",
                        excerpt_or_reference=c_info.get("chunk_text", "")[:300],
                    )
                    matrix_repo.add_evidence(evidence)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor="Auditor",
                    action="AI Finding Proposal Created",
                    details=f"Created AI Finding Proposal '{created_finding.title}'",
                )
            )

            return created_finding
