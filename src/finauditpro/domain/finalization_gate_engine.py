"""Domain evaluation engine for Phase D Finalization Gate and Open Items Aggregation."""

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
    FinalizationBlocker,
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
        subsequent_events_count: int,
        related_parties: RelatedPartyCompletionRecord | None,
        sa240_override: SA240CompletionRecord | None = None,
        **kwargs: Any,
    ) -> FinalizationGateResult:
        if sa240_override is None and "fraud" in kwargs:  # ignore
            sa240_override = kwargs["fraud"]  # ignore
        open_items: list[OpenItem] = []
        blockers: list[FinalizationBlocker] = []
        warnings: list[str] = []

        # 1. Review Notes Check
        for rn in review_notes:
            status_val = getattr(rn.status, "value", str(rn.status)).lower()
            if status_val not in ("cleared", "closed"):
                is_crit = "critical" in rn.note_text.lower() or "material" in rn.note_text.lower()
                sev = ItemSeverityEnum.CRITICAL if is_crit else ItemSeverityEnum.HIGH
                open_items.append(
                    OpenItem(
                        engagement_id=engagement_id,
                        source_type="Review Note",
                        source_ref=rn.id[:8],
                        title=f"Uncleared Review Note: {rn.note_text[:50]}",
                        description=rn.note_text,
                        severity=sev,
                        action_required="Provide response, evidence clearance, and clear note.",
                        is_blocking=True,
                    )
                )
                blockers.append(
                    FinalizationBlocker(
                        category="Review Notes",
                        reason=f"Open review note requires reviewer clearance: {rn.note_text[:60]}",
                        source_ref=f"RN-{rn.id[:8]}",
                        action_required="Resolve reviewer queries and mark cleared.",
                        severity=sev,
                    )
                )

        # 2. Audit Exceptions Check
        for exc in exceptions:
            status_val = getattr(exc.status, "value", str(exc.status)).lower()
            if status_val not in ("resolved", "cleared", "waived"):
                sev = ItemSeverityEnum.CRITICAL if exc.is_material else ItemSeverityEnum.HIGH
                open_items.append(
                    OpenItem(
                        engagement_id=engagement_id,
                        source_type="Audit Exception",
                        source_ref=exc.exception_number or exc.id[:8],
                        title=f"Unresolved Exception: {exc.title}",
                        description=exc.description or exc.title,
                        severity=sev,
                        action_required="Propose audit adjustment or document resolution justification.",
                        is_blocking=exc.is_material,
                    )
                )
                if exc.is_material:
                    blockers.append(
                        FinalizationBlocker(
                            category="Audit Exceptions",
                            reason=f"Unresolved material audit exception: {exc.title}",
                            source_ref=exc.exception_number or exc.id[:8],
                            action_required="Post adjusting entry or obtain partner waiver.",
                            severity=ItemSeverityEnum.CRITICAL,
                        )
                    )

        # 3. SA 450 Misstatements Check
        if sa450_summary and sa450_summary.total_uncorrected_misstatements > 0:
            if sa450_summary.is_material_in_aggregate or sa450_summary.is_material_individually:
                open_items.append(
                    OpenItem(
                        engagement_id=engagement_id,
                        source_type="SA 450 Misstatement",
                        source_ref="SA-450-AGGREGATE",
                        title="Uncorrected Misstatements Exceed Materiality Threshold",
                        description=(
                            f"Total uncorrected amount of ₹{sa450_summary.total_uncorrected_amount_paise / 100:,.2f} "
                            f"exceeds Materiality (₹{sa450_summary.overall_materiality_paise / 100:,.2f})."
                        ),
                        severity=ItemSeverityEnum.CRITICAL,
                        action_required="Obtain management adjustment or issue modified audit opinion.",
                        is_blocking=True,
                    )
                )
                blockers.append(
                    FinalizationBlocker(
                        category="Misstatement Evaluation",
                        reason="Uncorrected misstatements exceed materiality threshold.",
                        source_ref="SA-450-EVALUATION",
                        action_required="Request management correction or document opinion modification.",
                        severity=ItemSeverityEnum.CRITICAL,
                    )
                )

        # 4. Financial Statement Package & Data Drift Check
        if not fs_package:
            blockers.append(
                FinalizationBlocker(
                    category="Financial Statements",
                    reason="No Schedule III Financial Statement Package generated for engagement.",
                    source_ref="FS-PACKAGE-NONE",
                    action_required="Generate and review Schedule III Financial Statements.",
                    severity=ItemSeverityEnum.CRITICAL,
                )
            )
        elif fs_package.is_stale:
            blockers.append(
                FinalizationBlocker(
                    category="Financial Statements",
                    reason="Financial Statement Package is STALE due to post-generation data drift.",
                    source_ref=f"PKG-{fs_package.id[:8]}",
                    action_required="Re-evaluate Financial Statements against updated Adjusted Trial Balance.",
                    severity=ItemSeverityEnum.CRITICAL,
                )
            )

        # 5. CARO 2020 Working Papers Check
        for cw in caro_workpapers:
            app_val = getattr(cw.applicability, "value", str(cw.applicability)).lower()
            if "applicable" in app_val and "not applicable" not in app_val:
                ans_val = getattr(cw.report_answer, "value", str(cw.report_answer))
                conclusion = getattr(cw, "conclusion_text", getattr(cw, "conclusion", ""))
                clause_label = getattr(cw, "clause_title", getattr(cw, "clause_code", "CARO"))
                clause_ref = getattr(cw, "clause_code", getattr(cw, "clause", "CARO"))
                if not conclusion or not ans_val or ans_val == "Not Evaluated":
                    blockers.append(
                        FinalizationBlocker(
                            category="CARO 2020",
                            reason=f"CARO Clause {clause_label} is applicable but has no documented conclusion.",
                            source_ref=f"CARO-{clause_ref}",
                            action_required="Complete audit procedure, link evidence, and sign off conclusion.",
                            severity=ItemSeverityEnum.HIGH,
                        )
                    )

        # 6. Going Concern Assessment (SA 570)
        if not going_concern:
            blockers.append(
                FinalizationBlocker(
                    category="Going Concern (SA 570)",
                    reason="Mandatory SA 570 Going Concern assessment memo has not been completed.",
                    source_ref="SA-570-MEMO",
                    action_required="Perform 12-month solvency evaluation and obtain partner sign-off.",
                    severity=ItemSeverityEnum.CRITICAL,
                )
            )

        # 7. Management Representation Letter (SA 580)
        mrl_status = getattr(mrl.status, "value", str(mrl.status)) if mrl else ""
        if not mrl or mrl_status not in (
            MRLStatusEnum.SIGNED_AND_OBTAINED.value,
            MRLStatusEnum.SIGNED_BY_MANAGEMENT.value,
        ):
            blockers.append(
                FinalizationBlocker(
                    category="Written Representations (SA 580)",
                    reason="Signed Management Representation Letter (MRL) has not been obtained.",
                    source_ref="SA-580-MRL",
                    action_required="Obtain signed MRL from authorized company signatories.",
                    severity=ItemSeverityEnum.CRITICAL,
                )
            )

        # 8. Related Parties (SA 550) & SA 240 Procedures
        if not related_parties or not related_parties.is_completed:
            blockers.append(
                FinalizationBlocker(
                    category="Related Parties (SA 550)",
                    reason="SA 550 Related party identification and arm's length evaluation incomplete.",
                    source_ref="SA-550-WP",
                    action_required="Review related party register and verify Schedule III disclosures.",
                    severity=ItemSeverityEnum.HIGH,
                )
            )
        if not sa240_override or not sa240_override.is_completed:
            blockers.append(
                FinalizationBlocker(
                    category="SA 240 Procedures (Management Override)",
                    reason="SA 240 Management override of controls & journal entry testing incomplete.",
                    source_ref="SA-240-WP",
                    action_required="Execute mandatory journal entry testing and document conclusion.",
                    severity=ItemSeverityEnum.HIGH,
                )
            )

        # 9. Incomplete Checklist Items
        for ci in checklist_items:
            status_val = getattr(ci.status, "value", str(ci.status)).lower()
            if ci.is_applicable and status_val not in ("complete", "not applicable"):
                open_items.append(
                    OpenItem(
                        engagement_id=engagement_id,
                        source_type="Checklist Item",
                        source_ref=ci.id[:8],
                        title=f"{ci.category}: {ci.title}",
                        description=ci.description,
                        severity=ItemSeverityEnum.MEDIUM,
                        action_required="Complete required completion procedure.",
                        is_blocking=status_val == "blocked",
                    )
                )
                if status_val == "blocked":
                    blockers.append(
                        FinalizationBlocker(
                            category="Completion Checklist",
                            reason=f"Checklist item '{ci.title}' is marked as BLOCKED.",
                            source_ref=f"CHK-{ci.id[:8]}",
                            action_required=ci.notes or "Resolve item blocker.",
                            severity=ItemSeverityEnum.HIGH,
                        )
                    )

        critical_count = sum(1 for oi in open_items if oi.severity == ItemSeverityEnum.CRITICAL)
        is_finalizable = len(blockers) == 0

        return FinalizationGateResult(
            is_finalizable=is_finalizable,
            blockers=blockers,
            warnings=warnings,
            total_open_items=len(open_items),
            critical_items_count=critical_count,
        )
