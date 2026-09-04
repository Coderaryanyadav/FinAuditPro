"""Pure domain evaluation engines for Assertion Coverage Matrix and Audit Completeness Scoring."""

from typing import Any

from finauditpro.domain.audit_execution_entities import (
    AssertionCoverageMatrixLine,
    AssertionCoverageReport,
    AuditCompletenessReport,
    ExceptionStatusEnum,
)
from finauditpro.domain.audit_matrix_entities import AssertionEnum


def build_assertion_coverage_report(
    areas: list[str],
    risks: list[Any],
    procs: list[Any],
    evidences: list[Any],
) -> AssertionCoverageReport:
    """Pure domain function evaluating assertion coverage across audit areas."""
    eval_assertions = [
        AssertionEnum.EXISTENCE,
        AssertionEnum.COMPLETENESS,
        AssertionEnum.ACCURACY,
        AssertionEnum.VALUATION,
        AssertionEnum.CUT_OFF,
        AssertionEnum.RIGHTS_AND_OBLIGATIONS,
    ]
    lines: list[AssertionCoverageMatrixLine] = []
    gaps: list[str] = []

    for area in areas:
        for ass in eval_assertions:
            linked_r = [
                r.risk_code
                for r in risks
                if (
                    ass in r.assertions
                    or str(ass.value) in [str(getattr(a, "value", a)) for a in r.assertions]
                    or ass == r.assertion
                )
                and (
                    area.lower() in r.category.lower()
                    or area.lower() in r.description.lower()
                    or not r.category
                )
            ]
            linked_p = [
                p.procedure_code
                for p in procs
                if (
                    ass in p.assertions
                    or str(ass.value) in [str(getattr(a, "value", a)) for a in p.assertions]
                    or ass == p.assertion
                )
                and (
                    any(
                        r_code in linked_r
                        for r_code in [r.risk_code for r in risks if r.id in p.linked_risk_ids]
                    )
                    or area.lower() in p.objective.lower()
                    or not p.linked_risk_ids
                )
            ]
            ev_count = len([e for e in evidences if any(p_code in e.title for p_code in linked_p)])
            has_conc = any(p.conclusion for p in procs if p.procedure_code in linked_p)
            is_cov = bool(linked_p and has_conc)
            gap_msg = None
            if not linked_r:
                gap_msg = f"{area} ({ass.value}): No risk identified"
            elif not linked_p:
                gap_msg = f"{area} ({ass.value}): Risk identified without audit procedure"
            elif not has_conc:
                gap_msg = f"{area} ({ass.value}): Procedure executed without conclusion"

            if gap_msg:
                gaps.append(gap_msg)

            lines.append(
                AssertionCoverageMatrixLine(
                    account_or_area=area,
                    schedule_iii_category=area,
                    assertion=ass,
                    linked_risk_codes=linked_r,
                    linked_procedure_codes=linked_p,
                    evidence_count=ev_count,
                    has_conclusion=has_conc,
                    is_covered=is_cov,
                    gap_reason=gap_msg,
                )
            )

    tot = len(lines)
    cov = len([l for l in lines if l.is_covered])
    pct = round((cov / tot) * 100.0, 2) if tot > 0 else 0.0
    return AssertionCoverageReport(
        total_matrix_lines=tot,
        covered_lines=cov,
        gap_count=len(gaps),
        coverage_percentage=pct,
        gaps=gaps,
        lines=lines,
    )


def build_audit_completeness_report(
    engagement_id: str,
    risks: list[Any],
    procs: list[Any],
    evidences: list[Any],
    exceptions: list[Any],
    misstatements: list[Any],
) -> AuditCompletenessReport:
    """Pure domain function computing 6-factor deterministic completeness and orphan detection."""
    orphaned_risks = [
        r.risk_code for r in risks if not any(r.id in p.linked_risk_ids for p in procs)
    ]
    orphaned_procs = [p.procedure_code for p in procs if not p.linked_risk_ids]
    procs_missing_ev = [
        p.procedure_code
        for p in procs
        if getattr(p, "requires_evidence", True)
        and not any(e.procedure_id == p.id for e in evidences)
    ]
    procs_missing_conc = [p.procedure_code for p in procs if not p.conclusion]
    unresolved_excs = [
        e.exception_code
        for e in exceptions
        if not e.is_resolved and e.status != ExceptionStatusEnum.ESCALATED_TO_MISSTATEMENT
    ]
    unresolved_missts = [
        f"{m.account_code}: ₹{m.amount_paise / 100:,.2f}"
        for m in misstatements
        if not m.is_corrected
    ]

    risk_cov = (
        (len([r for r in risks if r.risk_code not in orphaned_risks]) / len(risks) * 100.0)
        if risks
        else 100.0
    )
    proc_exec = (
        (
            len(
                [
                    p
                    for p in procs
                    if str(getattr(p, "status", ""))
                    in ("Completed", "ProcedureStatusEnum.COMPLETED")
                ]
            )
            / len(procs)
            * 100.0
        )
        if procs
        else 100.0
    )
    ev_cov = (
        (len([p for p in procs if p.procedure_code not in procs_missing_ev]) / len(procs) * 100.0)
        if procs
        else 100.0
    )
    exc_res = (
        (
            len(
                [
                    e
                    for e in exceptions
                    if e.is_resolved or e.status == ExceptionStatusEnum.ESCALATED_TO_MISSTATEMENT
                ]
            )
            / len(exceptions)
            * 100.0
        )
        if exceptions
        else 100.0
    )
    misst_res = (
        (len([m for m in misstatements if m.is_corrected]) / len(misstatements) * 100.0)
        if misstatements
        else 100.0
    )
    rev_comp = (
        (
            len(
                [
                    p
                    for p in procs
                    if p.reviewer
                    or str(getattr(p, "status", ""))
                    in ("Completed", "ProcedureStatusEnum.COMPLETED")
                ]
            )
            / len(procs)
            * 100.0
        )
        if procs
        else 100.0
    )

    composite = round(
        (risk_cov * 0.20)
        + (proc_exec * 0.25)
        + (ev_cov * 0.15)
        + (exc_res * 0.15)
        + (misst_res * 0.15)
        + (rev_comp * 0.10),
        2,
    )
    is_ready = bool(
        composite >= 95.0 and not unresolved_excs and not orphaned_risks and not procs_missing_conc
    )

    return AuditCompletenessReport(
        engagement_id=engagement_id,
        risk_coverage_pct=round(risk_cov, 2),
        procedure_execution_pct=round(proc_exec, 2),
        evidence_coverage_pct=round(ev_cov, 2),
        exception_resolution_pct=round(exc_res, 2),
        misstatement_resolution_pct=round(misst_res, 2),
        review_completion_pct=round(rev_comp, 2),
        composite_completeness_score=composite,
        is_ready_for_finalization=is_ready,
        orphaned_risks=orphaned_risks,
        orphaned_procedures=orphaned_procs,
        procedures_missing_evidence=procs_missing_ev,
        procedures_missing_conclusion=procs_missing_conc,
        unresolved_exceptions=unresolved_excs,
        unresolved_misstatements=unresolved_missts,
    )
