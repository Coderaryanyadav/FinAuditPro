"""Prompt builder and citation extraction engine for local AI Copilot capabilities."""

import re
from typing import Any

from finauditpro.domain.ai_entities import (
    AICitation,
    AICopilotContext,
    AICopilotTaskTypeEnum,
)
from finauditpro.domain.prompt_engine import sanitize_untrusted_content


class CopilotPromptEngine:
    """Constructs focused, citation-enforced prompts for all AI Copilot capabilities."""

    COPILOT_PROMPT_VERSION = "2.0-copilot"

    @classmethod
    def build_copilot_prompt(
        cls,
        task_type: AICopilotTaskTypeEnum,
        user_prompt: str,
        context: AICopilotContext,
        retrieved_evidence: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Construct prompt enforcing contextual grounding and mandatory source object citations."""
        evidence_lines = []
        for c in retrieved_evidence:
            cid = c.get("chunk_id", c.get("evidence_id", "EVD-UNK"))
            title = c.get("title", "Document")
            page = c.get("page_number", 1)
            raw = c.get("chunk_text", c.get("excerpt", ""))
            safe_text = sanitize_untrusted_content(raw)
            evidence_lines.append(
                f"--- EVIDENCE SOURCE: [{cid}] | {title} (Page {page}) ---\n{safe_text}\n--- END SOURCE [{cid}] ---"
            )

        evidence_block = (
            "\n\n".join(evidence_lines) if evidence_lines else "NO DIRECT DOCUMENT CHUNKS RETRIEVED."
        )

        task_instructions = cls._get_task_specific_instructions(task_type)

        prompt_body = (
            f"SYSTEM ROLE: You are FinAuditPro Local AI Copilot, an offline statutory audit intelligence assistant for Indian statutory audits.\n"
            f"MANDATORY AUDIT GUARDRAILS:\n"
            f"1. Base your response STRICTLY on the engagement context and retrieved evidence sources below.\n"
            f"2. Every claim, observation, and calculation MUST cite the specific source object in square brackets, e.g. [WP-REV-004], [EVD-0092], [JV-18292], [RSK-01], or [CHUNK-101].\n"
            f"3. You CANNOT independently approve working papers, change official risk scores, or modify evidence. Your output is advisory.\n"
            f"4. Keep client data strictly local.\n\n"
            f"TASK TYPE: {task_type.value}\n"
            f"SPECIFIC INSTRUCTIONS:\n{task_instructions}\n\n"
            f"ENGAGEMENT CONTEXT:\n"
            f"• Firm: {context.firm_name} | Client: {context.client_name}\n"
            f"• Engagement: {context.engagement_title} (FY {context.financial_year}) [ID: {context.engagement_id}]\n"
            f"• Audit Area: {context.audit_area or 'General / Multi-area'}\n\n"
            f"ACTIVE AUDIT ARTIFACTS:\n"
            f"• Risks: {[r['risk_code'] + ' (' + r['title'] + ')' for r in context.active_risks]}\n"
            f"• Working Papers: {[w['index_reference'] + ' (' + w['title'] + ')' for w in context.active_working_papers]}\n"
            f"• Procedures: {[p['procedure_code'] + ' (' + p['objective'][:40] + '...)' for p in context.active_procedures]}\n"
            f"• Findings: {[f['title'] for f in context.active_findings]}\n"
            f"• Exceptions: {[e['title'] for e in context.active_exceptions]}\n\n"
            f"RETRIEVED EVIDENCE SOURCES:\n"
            f"{evidence_block}\n\n"
            f"AUDITOR REQUEST:\n"
            f"{sanitize_untrusted_content(user_prompt)}\n\n"
            f"Provide structured, cited response:"
        )

        return [{"role": "user", "content": prompt_body}]

    @classmethod
    def _get_task_specific_instructions(cls, task_type: AICopilotTaskTypeEnum) -> str:
        if task_type == AICopilotTaskTypeEnum.SUMMARIZE_EVIDENCE:
            return "Summarize key terms, monetary values, dates, and counterparties from the retrieved evidence. Explicitly cite each evidentiary source [EVD-XXX]."
        elif task_type == AICopilotTaskTypeEnum.EXPLAIN_EXCEPTIONS:
            return "Explain the deterministic root cause of the flagged exception under Indian Accounting Standards (AS/Ind AS) and ICAI SAs. Cite the transaction [JV-XXX] and rule."
        elif task_type == AICopilotTaskTypeEnum.SUMMARIZE_WORKING_PAPERS:
            return "Summarize the working paper's objective, population, sampling method, exceptions noted, and preliminary status. Cite working paper index [WP-XXX]."
        elif task_type == AICopilotTaskTypeEnum.DRAFT_REVIEW_NOTES:
            return "Draft structured, actionable review note points for Senior / Partner review. Identify potential testing gaps or unaddressed assertions."
        elif task_type == AICopilotTaskTypeEnum.SUGGEST_FOLLOW_UP_QUESTIONS:
            return "Draft targeted management inquiry / PBC (Provided by Client) questions. Be specific about missing documents, reconciliations, or explanations."
        elif task_type == AICopilotTaskTypeEnum.EXPLAIN_FINANCIAL_ANOMALIES:
            return "Analyze multi-period trends, ratio variances, or Benford deviations. Explain potential economic drivers vs misstatement risks."
        elif task_type == AICopilotTaskTypeEnum.SUGGEST_RELEVANT_PROCEDURES:
            return "Recommend substantive or control procedures under SA 315 / SA 330 based on the identified risks and assertions."
        return "Provide a clear, concise audit explanation with explicit artifact citations."

    @classmethod
    def extract_citations(cls, text: str, context: AICopilotContext, retrieved_evidence: list[dict[str, Any]]) -> list[AICitation]:
        """Parse square-bracket citations from generated text and map them to known artifacts."""
        citations: list[AICitation] = []
        found_tokens = re.findall(r"\[([A-Za-z0-9_\-\.\:\s]+)\]", text)
        seen_refs = set()

        # Build lookup tables
        wp_lookup = {w["index_reference"]: w for w in context.active_working_papers}
        risk_lookup = {r["risk_code"]: r for r in context.active_risks}
        proc_lookup = {p["procedure_code"]: p for p in context.active_procedures}
        evd_lookup = {e.get("chunk_id", e.get("evidence_id")): e for e in retrieved_evidence}

        for token in found_tokens:
            token_clean = token.strip()
            if token_clean in seen_refs:
                continue

            if token_clean in wp_lookup:
                w = wp_lookup[token_clean]
                citations.append(AICitation(
                    reference_id=token_clean,
                    artifact_type="WorkingPaper",
                    filename_or_title=w["title"],
                    excerpt=f"Area: {w['area']} | Status: {w['status']}",
                    relevance_score=0.95,
                ))
                seen_refs.add(token_clean)
            elif token_clean in risk_lookup:
                r = risk_lookup[token_clean]
                citations.append(AICitation(
                    reference_id=token_clean,
                    artifact_type="Risk",
                    filename_or_title=r["title"],
                    excerpt=f"Severity: {r['severity']} | Category: {r['category']}",
                    relevance_score=0.92,
                ))
                seen_refs.add(token_clean)
            elif token_clean in proc_lookup:
                p = proc_lookup[token_clean]
                citations.append(AICitation(
                    reference_id=token_clean,
                    artifact_type="Procedure",
                    filename_or_title=p["objective"][:50],
                    excerpt=f"Type: {p['procedure_type']} | Status: {p['status']}",
                    relevance_score=0.90,
                ))
                seen_refs.add(token_clean)
            elif token_clean in evd_lookup:
                e = evd_lookup[token_clean]
                citations.append(AICitation(
                    reference_id=token_clean,
                    artifact_type="EvidenceChunk",
                    filename_or_title=e.get("title", "Document"),
                    page_number=e.get("page_number", 1),
                    excerpt=e.get("chunk_text", e.get("excerpt", ""))[:150],
                    relevance_score=0.95,
                ))
                seen_refs.add(token_clean)
            elif any(token_clean.startswith(pfx) for pfx in ("WP-", "EVD-", "JV-", "RSK-", "PROC-", "INV-", "CHQ-")):
                citations.append(AICitation(
                    reference_id=token_clean,
                    artifact_type="AuditArtifactReference",
                    filename_or_title=f"Referenced Artifact {token_clean}",
                    excerpt=f"Cited directly in Copilot response: {token_clean}",
                    relevance_score=0.88,
                ))
                seen_refs.add(token_clean)

        return citations
