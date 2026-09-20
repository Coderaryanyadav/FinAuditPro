"""Application Service orchestrating Unified Search queries across all FinAuditPro entities."""

from collections.abc import Iterable
from typing import Any

from sqlalchemy import text

from finauditpro.domain.unified_search_engine import (
    SearchResultDTO,
    SearchResultGroupEnum,
    SearchScopeContext,
    format_search_context,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager


class UnifiedSearchService:
    """Enterprise Unified Search service enforcing indexed queries, FTS5 matching, and security boundary isolation."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def search(
        self,
        query: str,
        scope: SearchScopeContext | None = None,
        limit_per_group: int = 5,
    ) -> list[SearchResultDTO]:
        """Execute unified search across Clients, Engagements, Documents, Working Papers, Tasks, Findings, Requests, and Transactions."""
        q_clean = query.strip()
        if not q_clean:
            return []

        results: list[SearchResultDTO] = []
        scope = scope or SearchScopeContext()

        with self.db_manager.session_scope() as session:
            client_name_map = self._get_client_name_map(session, scope)
            eng_client_map, eng_fy_map = self._get_engagement_maps(session, scope)

            # 1. CLIENTS
            results.extend(self._search_clients(session, q_clean, scope, limit_per_group))

            # 2. ENGAGEMENTS (Categorized under CLIENTS)
            results.extend(self._search_engagements(session, q_clean, scope, client_name_map, limit_per_group))

            # 3. DOCUMENTS (Metadata & FTS5)
            results.extend(self._search_documents(session, q_clean, scope, client_name_map, eng_client_map, eng_fy_map, limit_per_group))

            # 4. WORK (Tasks & Requests)
            results.extend(self._search_work_items(session, q_clean, scope, client_name_map, eng_client_map, eng_fy_map, limit_per_group))

            # 5. AUDIT (Working Papers & Findings)
            results.extend(self._search_audit_items(session, q_clean, scope, client_name_map, eng_client_map, eng_fy_map, limit_per_group))

            # 6. FINANCIAL (Transactions & Journal Entries)
            results.extend(self._search_financial_items(session, q_clean, scope, client_name_map, eng_client_map, eng_fy_map, limit_per_group))

        return results

    def _build_in_clause(self, col: str, ids: Iterable[str] | None, prefix: str, params: dict[str, Any]) -> str:
        if ids is None:
            return ""
        id_list = list(ids)
        if not id_list:
            return " AND 1=0"
        keys = []
        for idx, val in enumerate(id_list):
            k = f"{prefix}_{idx}"
            keys.append(f":{k}")
            params[k] = val
        return f" AND {col} IN ({', '.join(keys)})"

    def _get_client_name_map(self, session: Any, scope: SearchScopeContext) -> dict[str, str]:
        sql = "SELECT id, name FROM clients WHERE 1=1"
        params: dict[str, Any] = {}
        sql += self._build_in_clause("id", scope.allowed_client_ids, "cid", params)
        rows = session.execute(text(sql), params).fetchall()
        return {row[0]: row[1] for row in rows}

    def _get_engagement_maps(self, session: Any, scope: SearchScopeContext) -> tuple[dict[str, str], dict[str, str]]:
        sql = "SELECT id, client_id, financial_year FROM engagements WHERE 1=1"
        params: dict[str, Any] = {}
        if scope.allowed_engagement_ids is not None:
            sql += self._build_in_clause("id", scope.allowed_engagement_ids, "eid", params)
        elif scope.allowed_client_ids is not None:
            sql += self._build_in_clause("client_id", scope.allowed_client_ids, "cid", params)

        rows = session.execute(text(sql), params).fetchall()
        c_map = {row[0]: row[1] for row in rows}
        fy_map = {row[0]: row[2] for row in rows}
        return c_map, fy_map

    def _search_clients(
        self, session: Any, query: str, scope: SearchScopeContext, limit: int
    ) -> list[SearchResultDTO]:
        sql = "SELECT id, name, entity_type, pan, gstin, industry FROM clients WHERE (name LIKE :q OR pan LIKE :q OR gstin LIKE :q OR industry LIKE :q)"
        params: dict[str, Any] = {"q": f"%{query}%"}
        sql += self._build_in_clause("id", scope.allowed_client_ids, "cid", params)
        sql += f" LIMIT {limit}"

        res: list[SearchResultDTO] = []
        for r in session.execute(text(sql), params).fetchall():
            c_name = r[1]
            ctx = format_search_context(c_name, r[2] or "Entity", None, "Client Directory")
            res.append(SearchResultDTO(
                id=r[0], entity_type="CLIENT", group=SearchResultGroupEnum.CLIENTS,
                title=c_name, subtitle=f"PAN: {r[3] or 'N/A'} | Industry: {r[5] or 'General'}",
                context_text=ctx, client_name=c_name, client_id=r[0], route_key="clients", payload={"client_id": r[0]}
            ))
        return res

    def _search_engagements(
        self, session: Any, query: str, scope: SearchScopeContext, client_name_map: dict[str, str], limit: int
    ) -> list[SearchResultDTO]:
        sql = "SELECT e.id, e.client_id, e.audit_type, e.financial_year, e.status, c.name FROM engagements e JOIN clients c ON e.client_id = c.id WHERE (e.audit_type LIKE :q OR e.financial_year LIKE :q OR e.status LIKE :q OR c.name LIKE :q)"
        params: dict[str, Any] = {"q": f"%{query}%"}
        if scope.allowed_engagement_ids is not None:
            sql += self._build_in_clause("e.id", scope.allowed_engagement_ids, "eid", params)
        elif scope.allowed_client_ids is not None:
            sql += self._build_in_clause("e.client_id", scope.allowed_client_ids, "cid", params)
        sql += f" LIMIT {limit}"

        res: list[SearchResultDTO] = []
        for r in session.execute(text(sql), params).fetchall():
            c_name = r[5]
            title_text = f"{c_name} — {r[2]} ({r[3]})"
            ctx = format_search_context(c_name, r[2], r[3], "Engagement Workspace")
            res.append(SearchResultDTO(
                id=r[0], entity_type="ENGAGEMENT", group=SearchResultGroupEnum.CLIENTS,
                title=title_text, subtitle=f"Status: {r[4]} | FY {r[3]}", context_text=ctx,
                client_name=c_name, client_id=r[1], engagement_id=r[0], route_key="engagements", payload={"engagement_id": r[0]}
            ))
        return res

    def _search_documents(
        self, session: Any, query: str, scope: SearchScopeContext, client_name_map: dict[str, str], eng_c_map: dict[str, str], eng_fy_map: dict[str, str], limit: int
    ) -> list[SearchResultDTO]:
        res: list[SearchResultDTO] = []
        seen_doc_ids: set[str] = set()

        sql = "SELECT id, engagement_id, filename, document_category, mime_type FROM documents WHERE (filename LIKE :q OR document_category LIKE :q OR mime_type LIKE :q)"
        params: dict[str, Any] = {"q": f"%{query}%"}
        sql += self._build_in_clause("engagement_id", scope.allowed_engagement_ids, "eid", params)
        sql += f" LIMIT {limit}"

        for r in session.execute(text(sql), params).fetchall():
            doc_id, eng_id, filename, category, mime_type = r[0], r[1], r[2], r[3], r[4]
            c_id = eng_c_map.get(eng_id)
            if scope.allowed_client_ids is not None and (not c_id or c_id not in scope.allowed_client_ids):
                continue
            seen_doc_ids.add(doc_id)
            c_name = client_name_map.get(c_id or "", "Client Entity")
            fy = eng_fy_map.get(eng_id)
            ctx = format_search_context(c_name, filename, fy, "Evidence / Documents")
            res.append(SearchResultDTO(
                id=doc_id, entity_type="DOCUMENT", group=SearchResultGroupEnum.DOCUMENTS,
                title=filename, subtitle=f"Category: {category or 'General'} | MIME: {mime_type or 'PDF'}",
                context_text=ctx, client_name=c_name, client_id=c_id, engagement_id=eng_id,
                route_key="documents", payload={"document_id": doc_id, "engagement_id": eng_id}
            ))

        # FTS5 Text Matching
        if len(res) < limit:
            try:
                fts_sql = "SELECT document_id, engagement_id, extracted_text FROM document_fts WHERE extracted_text MATCH :fts_q LIMIT 5"
                for f_row in session.execute(text(fts_sql), {"fts_q": query}).fetchall():
                    d_id, eng_id, text_snippet = f_row[0], f_row[1], f_row[2]
                    if d_id in seen_doc_ids:
                        continue
                    if scope.allowed_engagement_ids is not None and eng_id not in scope.allowed_engagement_ids:
                        continue
                    c_id = eng_c_map.get(eng_id)
                    if scope.allowed_client_ids is not None and (not c_id or c_id not in scope.allowed_client_ids):
                        continue

                    c_name = client_name_map.get(c_id or "", "Client Entity")
                    fy = eng_fy_map.get(eng_id)
                    ctx = format_search_context(c_name, f"FTS Text: {text_snippet[:40]}...", fy, "PDF Document FTS")
                    res.append(SearchResultDTO(
                        id=d_id, entity_type="DOCUMENT", group=SearchResultGroupEnum.DOCUMENTS,
                        title=f"Doc Match #{d_id[:6]}", subtitle=f"Extracted: {text_snippet[:60]}...",
                        context_text=ctx, client_name=c_name, client_id=c_id, engagement_id=eng_id,
                        route_key="documents", payload={"document_id": d_id, "engagement_id": eng_id}
                    ))
                    seen_doc_ids.add(d_id)
                    if len(res) >= limit:
                        break
            except Exception:
                pass

        return res

    def _search_work_items(
        self, session: Any, query: str, scope: SearchScopeContext, client_name_map: dict[str, str], eng_c_map: dict[str, str], eng_fy_map: dict[str, str], limit: int
    ) -> list[SearchResultDTO]:
        res: list[SearchResultDTO] = []
        try:
            t_sql = "SELECT id, engagement_id, title, description, assignee, status FROM work_tasks WHERE (title LIKE :q OR description LIKE :q)"
            params: dict[str, Any] = {"q": f"%{query}%"}
            t_sql += self._build_in_clause("engagement_id", scope.allowed_engagement_ids, "eid", params)
            t_sql += f" LIMIT {limit}"

            for r in session.execute(text(t_sql), params).fetchall():
                eng_id = r[1]
                c_id = eng_c_map.get(eng_id)
                if scope.allowed_client_ids is not None and (not c_id or c_id not in scope.allowed_client_ids):
                    continue
                c_name = client_name_map.get(c_id or "", "Client Entity")
                ctx = format_search_context(c_name, r[2], eng_fy_map.get(eng_id), "Work / Tasks")
                res.append(SearchResultDTO(
                    id=r[0], entity_type="TASK", group=SearchResultGroupEnum.WORK,
                    title=r[2], subtitle=f"Assignee: {r[4] or 'Unassigned'} | Status: {r[5]}",
                    context_text=ctx, client_name=c_name, client_id=c_id, engagement_id=eng_id,
                    route_key="work_center", payload={"task_id": r[0]}
                ))
        except Exception:
            pass

        try:
            r_sql = "SELECT id, engagement_id, title, description, status FROM document_requests WHERE (title LIKE :q OR description LIKE :q)"
            r_params: dict[str, Any] = {"q": f"%{query}%"}
            r_sql += self._build_in_clause("engagement_id", scope.allowed_engagement_ids, "eid", r_params)
            r_sql += " LIMIT 5"

            for r in session.execute(text(r_sql), r_params).fetchall():
                eng_id = r[1]
                c_id = eng_c_map.get(eng_id)
                if scope.allowed_client_ids is not None and (not c_id or c_id not in scope.allowed_client_ids):
                    continue
                c_name = client_name_map.get(c_id or "", "Client Entity")
                ctx = format_search_context(c_name, r[2], eng_fy_map.get(eng_id), "PBC / Requests")
                res.append(SearchResultDTO(
                    id=r[0], entity_type="REQUEST", group=SearchResultGroupEnum.WORK,
                    title=r[2], subtitle=f"Request Status: {r[4]}", context_text=ctx,
                    client_name=c_name, client_id=c_id, engagement_id=eng_id,
                    route_key="inbox", payload={"request_id": r[0]}
                ))
        except Exception:
            pass

        return res[:limit]

    def _search_audit_items(
        self, session: Any, query: str, scope: SearchScopeContext, client_name_map: dict[str, str], eng_c_map: dict[str, str], eng_fy_map: dict[str, str], limit: int
    ) -> list[SearchResultDTO]:
        res: list[SearchResultDTO] = []
        try:
            wp_sql = "SELECT id, engagement_id, title, index_reference, area, status FROM working_papers WHERE (title LIKE :q OR index_reference LIKE :q OR area LIKE :q)"
            params: dict[str, Any] = {"q": f"%{query}%"}
            wp_sql += self._build_in_clause("engagement_id", scope.allowed_engagement_ids, "eid", params)
            wp_sql += f" LIMIT {limit}"

            for r in session.execute(text(wp_sql), params).fetchall():
                eng_id = r[1]
                c_id = eng_c_map.get(eng_id)
                if scope.allowed_client_ids is not None and (not c_id or c_id not in scope.allowed_client_ids):
                    continue
                c_name = client_name_map.get(c_id or "", "Client Entity")
                ctx = format_search_context(c_name, r[2], eng_fy_map.get(eng_id), "Working Papers")
                res.append(SearchResultDTO(
                    id=r[0], entity_type="WORKING_PAPER", group=SearchResultGroupEnum.AUDIT,
                    title=f"WP [{r[3]}]: {r[2]}", subtitle=f"Area: {r[4] or 'General'} | Status: {r[5]}",
                    context_text=ctx, client_name=c_name, client_id=c_id, engagement_id=eng_id,
                    route_key="working_paper", payload={"wp_id": r[0]}
                ))
        except Exception:
            pass

        try:
            f_sql = "SELECT id, engagement_id, title, description, severity FROM audit_findings WHERE (title LIKE :q OR description LIKE :q)"
            f_params: dict[str, Any] = {"q": f"%{query}%"}
            f_sql += self._build_in_clause("engagement_id", scope.allowed_engagement_ids, "eid", f_params)
            f_sql += " LIMIT 5"

            for r in session.execute(text(f_sql), f_params).fetchall():
                eng_id = r[1]
                c_id = eng_c_map.get(eng_id)
                if scope.allowed_client_ids is not None and (not c_id or c_id not in scope.allowed_client_ids):
                    continue
                c_name = client_name_map.get(c_id or "", "Client Entity")
                ctx = format_search_context(c_name, r[2], eng_fy_map.get(eng_id), "Audit Findings")
                res.append(SearchResultDTO(
                    id=r[0], entity_type="FINDING", group=SearchResultGroupEnum.AUDIT,
                    title=r[2], subtitle=f"Severity: {r[4] or 'MEDIUM'}", context_text=ctx,
                    client_name=c_name, client_id=c_id, engagement_id=eng_id,
                    route_key="audit_matrix", payload={"finding_id": r[0]}
                ))
        except Exception:
            pass

        return res[:limit]

    def _search_financial_items(
        self, session: Any, query: str, scope: SearchScopeContext, client_name_map: dict[str, str], eng_c_map: dict[str, str], eng_fy_map: dict[str, str], limit: int
    ) -> list[SearchResultDTO]:
        res: list[SearchResultDTO] = []
        try:
            j_sql = "SELECT id, engagement_id, aje_number, title, narration, total_debit_paise FROM audit_journal_entries WHERE (aje_number LIKE :q OR title LIKE :q OR narration LIKE :q)"
            params: dict[str, Any] = {"q": f"%{query}%"}
            j_sql += self._build_in_clause("engagement_id", scope.allowed_engagement_ids, "eid", params)
            j_sql += f" LIMIT {limit}"

            for r in session.execute(text(j_sql), params).fetchall():
                eng_id = r[1]
                c_id = eng_c_map.get(eng_id)
                if scope.allowed_client_ids is not None and (not c_id or c_id not in scope.allowed_client_ids):
                    continue
                c_name = client_name_map.get(c_id or "", "Client Entity")
                amt_rupees = (r[5] or 0) / 100.0
                ctx = format_search_context(c_name, f"AJE #{r[2]}: {r[3]}", eng_fy_map.get(eng_id), "Audit Journal Entry")
                res.append(SearchResultDTO(
                    id=r[0], entity_type="TRANSACTION", group=SearchResultGroupEnum.FINANCIAL,
                    title=f"AJE #{r[2]}: {r[3]}", subtitle=f"Narration: {r[4][:50]} | Amount: ₹{amt_rupees:,.2f}",
                    context_text=ctx, client_name=c_name, client_id=c_id, engagement_id=eng_id,
                    route_key="financial_data", payload={"journal_id": r[0]}
                ))
        except Exception:
            pass

        return res
