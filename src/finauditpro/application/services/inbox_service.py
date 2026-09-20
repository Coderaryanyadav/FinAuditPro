"""Application service managing unified Practice Inbox intake, classification review, and human approval."""

from datetime import UTC, datetime

from finauditpro.application.dtos_inbox import (
    InboxFilterDTO,
    InboxItemDTO,
    InboxSummaryDTO,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import (
    ClientModel,
    DocumentModel,
    EngagementModel,
)


class InboxService:
    """Service orchestrating Practice Inbox queries and human-in-the-loop document classification approval."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_inbox_items(self, filter_dto: InboxFilterDTO | None = None) -> InboxSummaryDTO:
        """Queries and aggregates Practice Inbox items based on filter criteria."""
        if filter_dto is None:
            filter_dto = InboxFilterDTO()

        with self.db_manager.session_scope() as session:
            # Load clients and engagements mapping
            clients = session.query(ClientModel).all()
            engagements = session.query(EngagementModel).all()

            client_map = {c.id: c for c in clients}
            eng_map = {e.id: e for e in engagements}

            items: list[InboxItemDTO] = []

            # 1. Fetch Evidence Documents
            docs_q = session.query(DocumentModel)
            if filter_dto.engagement_id:
                docs_q = docs_q.filter(DocumentModel.engagement_id == filter_dto.engagement_id)
            elif filter_dto.client_id:
                client_eng_ids = [e.id for e in engagements if e.client_id == filter_dto.client_id]
                docs_q = docs_q.filter(DocumentModel.engagement_id.in_(client_eng_ids))

            docs = docs_q.order_by(DocumentModel.uploaded_at.desc()).all()

            for doc in docs:
                eng = eng_map.get(doc.engagement_id)
                c_id = eng.client_id if eng else ""
                client = client_map.get(c_id)

                c_name = client.name if client else "Practice Client"
                fy = eng.financial_year if eng else "—"

                dt = doc.uploaded_at if isinstance(doc.uploaded_at, datetime) else datetime.now(UTC)
                conf = doc.category_confidence if doc.category_confidence is not None else 0.85
                cat = doc.human_category or doc.machine_category or doc.document_category or "Unclassified"

                # Infer status and human approval state
                raw_status = str(doc.status).upper()
                if raw_status in ("ACCEPTED", "APPROVED"):
                    status = "ACCEPTED"
                    approval_state = "APPROVED" if not doc.human_category else "OVERRIDDEN"
                elif raw_status == "REJECTED":
                    status = "REJECTED"
                    approval_state = "REJECTED"
                elif conf < 0.90 or cat == "Unclassified" or raw_status in ("DRAFT", "NEEDS_REVIEW"):
                    status = "NEEDS_REVIEW"
                    approval_state = "PENDING"
                else:
                    status = "CLASSIFIED"
                    approval_state = "PENDING"

                item = InboxItemDTO(
                    id=doc.id,
                    item_type="DOCUMENT" if conf >= 0.80 else "AI_SUGGESTION",
                    title=doc.filename,
                    client_id=c_id,
                    client_name=c_name,
                    engagement_id=doc.engagement_id,
                    financial_year=fy,
                    received_time=dt,
                    detected_category=cat,
                    confidence_score=conf,
                    status=status,
                    reasoning_evidence=doc.category_reasoning,
                    model_info="LM Studio Rule/LLM Classifier",
                    human_approval_state=approval_state,
                    target_route="documents",
                    file_path=doc.stored_path,
                    file_size_bytes=doc.file_size_bytes,
                    mime_type=doc.mime_type,
                )
                items.append(item)

            # 2. Fetch PBC Requests / Items
            try:
                from finauditpro.infrastructure.persistence.pbc_and_query_models import (
                    ClientDocumentRequestModel,
                )

                pbc_reqs = session.query(ClientDocumentRequestModel).all()

                for req in pbc_reqs:
                    eng = eng_map.get(req.engagement_id)
                    c_id = eng.client_id if eng else ""
                    client = client_map.get(c_id)
                    c_name = client.name if client else "Practice Client"
                    fy = eng.financial_year if eng else "—"

                    st = str(req.status).upper()
                    item_st = "ACCEPTED" if st in ("RECEIVED", "APPROVED", "CONFIRMED") else "NEEDS_REVIEW"
                    dt = req.updated_at if isinstance(req.updated_at, datetime) else datetime.now(UTC)
                    items.append(
                        InboxItemDTO(
                            id=req.id,
                            item_type="PBC_REQUEST",
                            title=req.title,
                            client_id=c_id,
                            client_name=c_name,
                            engagement_id=req.engagement_id,
                            financial_year=fy,
                            received_time=dt,
                            detected_category="PBC Document Request",
                            confidence_score=1.0,
                            status=item_st,
                            reasoning_evidence=req.description,
                            model_info="Client Intake Pipeline",
                            human_approval_state="APPROVED" if item_st == "ACCEPTED" else "PENDING",
                            target_route="pbc",
                        )
                    )
            except Exception:
                pass

            # Calculate Sub-Counts
            total_items = len(items)
            needs_review_count = sum(1 for i in items if i.status == "NEEDS_REVIEW")
            documents_count = sum(1 for i in items if i.item_type in ("DOCUMENT", "AI_SUGGESTION"))
            requests_count = sum(1 for i in items if i.item_type == "PBC_REQUEST")
            ai_suggestions_count = sum(1 for i in items if i.item_type == "AI_SUGGESTION" or i.confidence_score < 0.90)

            # Apply Filter Tab
            filtered_items = items
            tab = filter_dto.tab.upper()
            if tab == "NEEDS_REVIEW":
                filtered_items = [i for i in items if i.status == "NEEDS_REVIEW"]
            elif tab == "DOCUMENTS":
                filtered_items = [i for i in items if i.item_type in ("DOCUMENT", "AI_SUGGESTION")]
            elif tab == "REQUESTS":
                filtered_items = [i for i in items if i.item_type == "PBC_REQUEST"]
            elif tab == "AI_SUGGESTIONS":
                filtered_items = [i for i in items if i.item_type == "AI_SUGGESTION" or i.confidence_score < 0.90]

            # Apply Search Query
            if filter_dto.search_query:
                q_str = filter_dto.search_query.lower()
                filtered_items = [
                    i for i in filtered_items
                    if q_str in i.title.lower() or q_str in i.client_name.lower() or q_str in i.detected_category.lower()
                ]

            return InboxSummaryDTO(
                total_items=total_items,
                needs_review_count=needs_review_count,
                documents_count=documents_count,
                requests_count=requests_count,
                ai_suggestions_count=ai_suggestions_count,
                items=filtered_items,
            )

    def accept_classification(self, doc_id: str, human_category: str | None = None) -> bool:
        """Human approval action to accept or override an AI document classification."""
        with self.db_manager.session_scope() as session:
            doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            if not doc:
                return False

            if human_category:
                doc.human_category = human_category
                doc.document_category = human_category
            elif doc.machine_category:
                doc.human_category = doc.machine_category
                doc.document_category = doc.machine_category

            doc.status = "Accepted"
            session.commit()
            return True

    def reject_item(self, doc_id: str, reason: str = "") -> bool:
        """Human rejection action for an inbox document item."""
        with self.db_manager.session_scope() as session:
            doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            if not doc:
                return False

            doc.status = "Rejected"
            doc.failure_reason = reason
            session.commit()
            return True
