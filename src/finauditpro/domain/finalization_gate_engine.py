"""Pure domain evaluation engine for Phase D Finalization Gate, Consistency Checks, and Open Items Aggregation."""

from typing import Any

from finauditpro.domain.audit_completion_entities import (
    GoingConcernAssessment,
    ManagementRepresentationLetter,
    MRLStatusEnum,
    SA450EvaluationSummary,
)
from finauditpro.domain.audit_execution_entities import AuditException, AuditMisstatement
from finauditpro.domain.completion_checklist_entities import (
    CompletionChecklistItem,
    FinalisationBlocker,
    FinalisationGateStatusEnum,
    FinalizationGateResult,
    ItemSeverityEnum,
    OpenItem,
    RelatedPartyCompletionRecord,
    SA240CompletionRecord,
)
from finauditpro.domain.compliance_entities import CAROClauseWorkpaper
from finauditpro.domain.financial_statement_entities import FinancialStatementPackage
from finauditpro.domain.working_paper_entities import ReviewNote


class FinalizationGateEngine:
    """Pure domain evaluation engine assessing finalization readiness and aggregating open items."""

    @staticmethod
    def evaluate(
        engagement_id: str,
        review_notes: list[ReviewNote],
        exceptions: list[AuditException],
        misstatements: list[AuditMisstatement],
        sa450_summary: SA450EvaluationSummary | None,
        fs_package: FinancialStatementPackage | None,
        caro_workpapers: list[CAROClauseWorkpaper],
        checklist_items: list[CompletionChecklistItem],
        going_concern: GoingConcernAssessment | None,
        mrl: ManagementRepresentationLetter | None,
        subsequent_events_count: int = 0,
        related_parties: RelatedPartyCompletionRecord | None = None,
        sa240_override: SA240CompletionRecord | None = None,
        working_papers: list[Any] | None = None,
        procedures: list[Any] | None = None,
        risks: list[Any] | None = None,
        findings: list[Any] | None = None,
        materiality: Any | None = None,
        bank_reconciliation_difference_paise: int = 0,
        missing_evidence_count: int = 0,
        tb_is_balanced: bool = True,
        discrepancies: list[str] | None = None,
        **kwargs: Any,
    ) -> FinalizationGateResult:
        if sa240_override is None and "fraud" in kwargs:  # ignore
            sa240_override = kwargs["fraud"]  # ignore

        open_items: list[OpenItem] = []
        blockers: list[FinalisationBlocker] = []
        reasons: list[str] = []

        # 1. Working Papers Check
        if working_papers:
            pending_wps = [
                w for w in working_papers
                if getattr(w.status, "value", str(w.status)).lower() not in ("approved", "locked", "closed", "reviewed")
            ]
            if pending_wps:
                cnt = len(pending_wps)
                r = f"{cnt} working paper{'s' if cnt != 1 else ''} pending review"
                reasons.append(r)
                blockers.append(FinalisationBlocker(category="Working Papers", reason=r, source_ref=f"WP-PENDING-{cnt}", action_required="Obtain sign-off.", severity=ItemSeverityEnum.CRITICAL))

        # 2. Review Notes Check
        open_notes = [rn for rn in review_notes if getattr(rn.status, "value", str(rn.status)).lower() not in ("cleared", "closed")]
        for rn in open_notes:
            sev = ItemSeverityEnum.CRITICAL if ("critical" in rn.note_text.lower() or "material" in rn.note_text.lower()) else ItemSeverityEnum.HIGH
            open_items.append(OpenItem(engagement_id=engagement_id, source_type="Review Note", source_ref=f"RN-{rn.id[:8]}", title=f"Uncleared Review Note: {rn.note_text[:50]}", description=rn.note_text, severity=sev, action_required="Clear note.", is_blocking=True))
            blockers.append(FinalisationBlocker(category="Review Notes", reason=f"Open review note requires clearance: {rn.note_text[:60]}", source_ref=f"RN-{rn.id[:8]}", action_required="Clear note.", severity=sev))
        if open_notes:
            cnt = len(open_notes)
            reasons.append(f"{cnt} unresolved review note{'s' if cnt != 1 else ''}")

        # 3. High-Risk Findings & Open Findings Check
        high_risk_findings = []
        if findings:
            for f in findings:
                if getattr(f.status, "value", str(f.status)).lower() not in ("resolved", "closed", "cleared", "waived"):
                    if getattr(f.severity, "value", str(f.severity)).lower() in ("high", "critical"):
                        high_risk_findings.append(f)
        if high_risk_findings:
            cnt = len(high_risk_findings)
            r = f"{cnt} high-risk finding{'s' if cnt != 1 else ''} unresolved"
            reasons.append(r)
            blockers.append(FinalisationBlocker(category="High-Risk Findings", reason=r, source_ref=f"FND-HIGH-{cnt}", action_required="Resolve high-risk findings.", severity=ItemSeverityEnum.CRITICAL))

        # 4. Bank Reconciliation Difference Check
        if bank_reconciliation_difference_paise > 0:
            diff_fmt = f"₹{bank_reconciliation_difference_paise // 100:,.0f}" if bank_reconciliation_difference_paise % 100 == 0 else f"₹{bank_reconciliation_difference_paise / 100:,.2f}"
            r = f"{diff_fmt} bank reconciliation difference"
            reasons.append(r)
            blockers.append(FinalisationBlocker(category="Bank Reconciliation", reason=r, source_ref="BRS-DIFF", action_required="Reconcile bank balance.", severity=ItemSeverityEnum.CRITICAL))

        # 5. Required Evidence Present Check
        if missing_evidence_count > 0:
            r = f"{missing_evidence_count} missing evidence item{'s' if missing_evidence_count != 1 else ''}"
            reasons.append(r)
            blockers.append(FinalisationBlocker(category="Audit Evidence", reason=r, source_ref=f"EVD-MISSING-{missing_evidence_count}", action_required="Attach evidence.", severity=ItemSeverityEnum.HIGH))

        # 6. Exceptions Check
        for exc in exceptions:
            if getattr(exc.status, "value", str(exc.status)).lower() not in ("resolved", "cleared", "waived"):
                is_mat = bool(getattr(exc, "is_material", False))
                sev = ItemSeverityEnum.CRITICAL if is_mat else ItemSeverityEnum.HIGH
                open_items.append(OpenItem(engagement_id=engagement_id, source_type="Audit Exception", source_ref=getattr(exc, "exception_number", exc.id[:8]), title=f"Unresolved Exception: {exc.title}", description=exc.description or exc.title, severity=sev, action_required="Resolve exception.", is_blocking=is_mat))
                if is_mat:
                    blockers.append(FinalisationBlocker(category="Audit Exceptions", reason=f"Unresolved material audit exception: {exc.title}", source_ref=exc.id[:8], action_required="Resolve exception.", severity=ItemSeverityEnum.CRITICAL))

        # 7. Materiality Documented Check
        mat_val = (getattr(materiality, "overall_materiality_paise", 0) or getattr(materiality, "overall_materiality", 0)) if materiality else 0
        if materiality is None or mat_val <= 0:
            reasons.append("Materiality assessment (SA 320) not documented")
            blockers.append(FinalisationBlocker(category="Materiality", reason="Mandatory SA 320 materiality calculation not established.", source_ref="SA-320-MATERIALITY", action_required="Establish materiality.", severity=ItemSeverityEnum.CRITICAL))

        # 8. Trial Balance & Financial Statements Reconciliation Check
        if not tb_is_balanced:
            reasons.append("Trial Balance is out of balance (Total Debit != Total Credit)")
            blockers.append(FinalisationBlocker(category="Trial Balance", reason="Trial Balance out of balance.", source_ref="TB-UNBALANCED", action_required="Balance TB.", severity=ItemSeverityEnum.CRITICAL))

        if not fs_package:
            blockers.append(FinalisationBlocker(category="Financial Statements", reason="No Schedule III Financial Statement Package generated.", source_ref="FS-PACKAGE-NONE", action_required="Generate statements.", severity=ItemSeverityEnum.CRITICAL))
        elif getattr(fs_package, "is_stale", False):
            reasons.append("Financial statements package is STALE due to post-generation data drift")
            blockers.append(FinalisationBlocker(category="Financial Statements", reason="Package is STALE.", source_ref=f"PKG-{fs_package.id[:8]}", action_required="Re-evaluate FS.", severity=ItemSeverityEnum.CRITICAL))

        # 9. Required Procedures Completed Check
        if procedures:
            incomp = [p for p in procedures if getattr(p.status, "value", str(p.status)).lower() not in ("completed", "closed", "approved")]
            if incomp:
                cnt = len(incomp)
                r = f"{cnt} required audit procedure{'s' if cnt != 1 else ''} incomplete"
                reasons.append(r)
                blockers.append(FinalisationBlocker(category="Audit Procedures", reason=r, source_ref=f"PROC-INCOMP-{cnt}", action_required="Complete procedures.", severity=ItemSeverityEnum.HIGH))

        # 10. SA 450 Misstatements Check
        if sa450_summary and sa450_summary.total_uncorrected_misstatements > 0 and (sa450_summary.is_material_in_aggregate or sa450_summary.is_material_individually):
            blockers.append(FinalisationBlocker(category="Misstatement Evaluation", reason="Uncorrected misstatements exceed materiality threshold.", source_ref="SA-450-EVALUATION", action_required="Obtain adjustment or modify opinion.", severity=ItemSeverityEnum.CRITICAL))

        # 11. CARO 2020 Check
        for cw in caro_workpapers:
            app_val = getattr(cw.applicability, "value", str(cw.applicability)).lower()
            if "applicable" in app_val and "not applicable" not in app_val:
                ans_val = getattr(cw.report_answer, "value", str(cw.report_answer))
                conclusion = getattr(cw, "conclusion_text", getattr(cw, "conclusion", ""))
                if not conclusion or not ans_val or ans_val == "Not Evaluated":
                    blockers.append(FinalisationBlocker(category="CARO 2020", reason=f"CARO Clause {getattr(cw, 'clause_code', 'CARO')} has no documented conclusion.", source_ref="CARO-CLAUSE", action_required="Complete CARO procedure.", severity=ItemSeverityEnum.HIGH))

        # 12. Statutory Standards (SA 570, SA 580, SA 550, SA 240)
        if not going_concern:
            blockers.append(FinalisationBlocker(category="Going Concern (SA 570)", reason="Mandatory SA 570 Going Concern assessment memo missing.", source_ref="SA-570-MEMO", action_required="Complete SA 570 memo.", severity=ItemSeverityEnum.CRITICAL))

        mrl_status = getattr(mrl.status, "value", str(mrl.status)) if mrl else ""
        if not mrl or mrl_status not in (MRLStatusEnum.SIGNED_AND_OBTAINED.value, MRLStatusEnum.SIGNED_BY_MANAGEMENT.value, "Signed Representation Letter Obtained", "Signed by Management"):
            blockers.append(FinalisationBlocker(category="Written Representations (SA 580)", reason="Signed Management Representation Letter (MRL) missing.", source_ref="SA-580-MRL", action_required="Obtain signed MRL.", severity=ItemSeverityEnum.CRITICAL))

        if not related_parties or not related_parties.is_completed:
            blockers.append(FinalisationBlocker(category="Related Parties (SA 550)", reason="SA 550 Related party identification incomplete.", source_ref="SA-550-WP", action_required="Complete SA 550 WP.", severity=ItemSeverityEnum.HIGH))

        if not sa240_override or not sa240_override.is_completed:
            blockers.append(FinalisationBlocker(category="SA 240 Procedures", reason="SA 240 Management override testing incomplete.", source_ref="SA-240-WP", action_required="Complete SA 240 testing.", severity=ItemSeverityEnum.HIGH))

        if discrepancies:
            for d in discrepancies:
                blockers.append(FinalisationBlocker(category="Reporting Reconciliation", reason=d, source_ref="REP-DISC", action_required="Reconcile discrepancy.", severity=ItemSeverityEnum.CRITICAL))

        # 13. Checklist Blocked Items
        for ci in checklist_items:
            if ci.is_applicable and getattr(ci.status, "value", str(ci.status)).lower() == "blocked":
                blockers.append(FinalisationBlocker(category="Completion Checklist", reason=f"Checklist item '{ci.title}' is marked BLOCKED.", source_ref=f"CHK-{ci.id[:8]}", action_required="Unblock checklist item.", severity=ItemSeverityEnum.HIGH))

        is_finalizable = len(blockers) == 0
        gate_status = FinalisationGateStatusEnum.READY if is_finalizable else FinalisationGateStatusEnum.BLOCKED
        summary_headline = "FINALISATION READY" if is_finalizable else "FINALISATION BLOCKED"
        display_text = "FINALISATION READY\n\nAll 10 mandatory audit gates and statutory consistency checks satisfied." if is_finalizable else f"FINALISATION BLOCKED\n\n" + ("\n".join(reasons) if reasons else "\n".join(f"• [{b.category}] {b.reason}" for b in blockers))

        return FinalizationGateResult(
            is_finalizable=is_finalizable,
            status=gate_status,
            summary_headline=summary_headline,
            display_text=display_text,
            formatted_reasons=reasons,
            blockers=blockers,
            open_items=open_items,
            total_open_items=len(open_items),
            critical_items_count=sum(1 for b in blockers if b.severity == ItemSeverityEnum.CRITICAL),
            gate_breakdown={
                "working_papers_complete": not any(b.category == "Working Papers" for b in blockers),
                "review_notes_resolved": not any(b.category == "Review Notes" for b in blockers),
                "required_evidence_present": not any(b.category == "Audit Evidence" for b in blockers),
                "high_risk_areas_addressed": not any(b.category == "High-Risk Findings" for b in blockers),
                "materiality_documented": not any(b.category == "Materiality" for b in blockers),
                "financial_statements_reconciled": not any(b.category in ("Trial Balance", "Bank Reconciliation", "Financial Statements") for b in blockers),
                "open_findings_addressed": len(high_risk_findings) == 0,
                "required_procedures_completed": not any(b.category == "Audit Procedures" for b in blockers),
                "reporting_checks_completed": not any(b.category in ("CARO 2020", "Going Concern (SA 570)", "Written Representations (SA 580)", "Reporting Reconciliation") for b in blockers),
            },
        )
