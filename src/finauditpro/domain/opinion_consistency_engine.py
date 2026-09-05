"""Pure domain engine evaluating audit opinion consistency, cross-document discrepancies,
candidate Key Audit Matters (KAMs), and report dependency hashes (Phase E).

Strictly adheres to ICAI SAs:
- SA 700: Forming an Opinion and Reporting on Financial Statements
- SA 705: Modifications to the Opinion in the Independent Auditor's Report
- SA 706: Emphasis of Matter Paragraphs and Other Matter Paragraphs
- SA 701: Communicating Key Audit Matters in the Independent Auditor's Report
- SA 570: Going Concern reporting consistency
- SA 560: Subsequent Events reporting consistency
"""

import hashlib
import json
from typing import Any

from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    CandidateKAMSourceEnum,
    ConsistencyIssue,
    KeyAuditMatter,
    OpinionFactorEnum,
)


class OpinionEvaluationResult:
    def __init__(
        self,
        is_consistent: bool,
        review_required: bool,
        identified_factors: list[OpinionFactorEnum],
        suggested_assessment: str,
        explanation: str,
    ) -> None:
        self.is_consistent = is_consistent
        self.review_required = review_required
        self.identified_factors = identified_factors
        self.suggested_assessment = suggested_assessment
        self.explanation = explanation


class OpinionConsistencyEngine:
    """Domain logic providing decision support and cross-document reconciliation for audit reports."""

    @staticmethod
    def evaluate_opinion_consistency(
        proposed_opinion: AuditOpinionTypeEnum,
        materiality_paise: int,
        uncorrected_misstatements_paise: int,
        has_scope_limitation: bool,
        is_scope_limitation_pervasive: bool,
        has_going_concern_uncertainty: bool,
        is_going_concern_disclosed: bool,
    ) -> OpinionEvaluationResult:
        """Evaluate whether proposed opinion is structurally consistent with underlying audit facts.

        Note: The software NEVER automatically changes an opinion. It provides decision support.
        """
        factors: list[OpinionFactorEnum] = []
        is_material_misstatement = uncorrected_misstatements_paise >= materiality_paise and materiality_paise > 0
        is_pervasive_misstatement = (
            uncorrected_misstatements_paise >= (materiality_paise * 3) and materiality_paise > 0
        )

        if is_material_misstatement:
            factors.append(OpinionFactorEnum.MATERIAL_MISSTATEMENT)
            if is_pervasive_misstatement:
                factors.append(OpinionFactorEnum.MATERIAL_AND_PERVASIVE)
            else:
                factors.append(OpinionFactorEnum.MATERIAL_NOT_PERVASIVE)

        if has_scope_limitation:
            factors.append(OpinionFactorEnum.SCOPE_LIMITATION)
            if is_scope_limitation_pervasive:
                factors.append(OpinionFactorEnum.MATERIAL_AND_PERVASIVE)
            else:
                factors.append(OpinionFactorEnum.MATERIAL_NOT_PERVASIVE)

        if has_going_concern_uncertainty:
            factors.append(OpinionFactorEnum.GOING_CONCERN_UNCERTAINTY)

        review_required = False
        suggested_assessment = "Proposed opinion appears consistent with evaluated audit evidence."
        explanation = "No contradictory indicators detected."

        if proposed_opinion == AuditOpinionTypeEnum.UNMODIFIED:
            if is_pervasive_misstatement:
                review_required = True
                suggested_assessment = "Review Required: Uncorrected misstatement is material and pervasive. SA 705 suggests consideration of an Adverse Opinion."
                explanation = f"Uncorrected misstatement ({uncorrected_misstatements_paise} paise) exceeds pervasive threshold vs materiality ({materiality_paise} paise)."
            elif is_material_misstatement:
                review_required = True
                suggested_assessment = "Review Required: Uncorrected misstatement is material but not pervasive. SA 705 suggests consideration of a Qualified Opinion."
                explanation = f"Uncorrected misstatement ({uncorrected_misstatements_paise} paise) exceeds overall materiality ({materiality_paise} paise)."
            elif has_scope_limitation:
                review_required = True
                if is_scope_limitation_pervasive:
                    suggested_assessment = "Review Required: Pervasive scope limitation present. SA 705 suggests consideration of a Disclaimer of Opinion."
                else:
                    suggested_assessment = "Review Required: Scope limitation present. SA 705 suggests consideration of a Qualified Opinion."
                explanation = "Inability to obtain sufficient appropriate audit evidence recorded."
            elif has_going_concern_uncertainty and not is_going_concern_disclosed:
                review_required = True
                suggested_assessment = "Review Required: Going concern material uncertainty identified but adequate disclosure not confirmed in Financial Statements."
                explanation = "SA 570 requires qualified or adverse opinion if going concern disclosure is inadequate."

        is_consistent = not review_required
        return OpinionEvaluationResult(
            is_consistent=is_consistent,
            review_required=review_required,
            identified_factors=factors,
            suggested_assessment=suggested_assessment,
            explanation=explanation,
        )

    @staticmethod
    def detect_candidate_kams(
        significant_risks: list[dict[str, Any]],
        major_audit_adjustments: list[dict[str, Any]],
        materiality_paise: int,
    ) -> list[KeyAuditMatter]:
        """Surface candidate Key Audit Matters based on existing engagement risks and adjustments.

        Crucial: Candidates are labeled SYSTEM-SUGGESTED CANDIDATE and require auditor adoption.
        """
        candidates: list[KeyAuditMatter] = []

        for risk in significant_risks:
            r_level = str(risk.get("risk_level", "")).upper()
            if "HIGH" in r_level or "CRITICAL" in r_level or "SIGNIFICANT" in r_level:
                candidates.append(
                    KeyAuditMatter(
                        matter_title=f"Assessment of {risk.get('title', 'Significant Risk Area')}",
                        why_significant=f"[SYSTEM-SUGGESTED CANDIDATE] Identified as significant audit risk ({risk.get('risk_level')}) requiring extensive audit procedures and management judgment.",
                        how_addressed=f"Audit procedures directed at assertion(s): {risk.get('assertion', 'Completeness / Valuation')}.",
                        fs_reference=f"Note reference for {risk.get('area', 'Financial Statement area')}",
                        wp_references=[str(risk.get("id", "WP-RISK"))],
                        is_candidate=True,
                        candidate_source=CandidateKAMSourceEnum.SIGNIFICANT_RISK,
                    )
                )

        for aje in major_audit_adjustments:
            amt = int(aje.get("amount_paise", 0))
            if amt >= (materiality_paise // 2) and materiality_paise > 0:
                candidates.append(
                    KeyAuditMatter(
                        matter_title=f"Material Audit Adjustment: {aje.get('description', 'Adjustment')}",
                        why_significant=f"[SYSTEM-SUGGESTED CANDIDATE] Audit adjustment of {amt} paise represents a significant proportion of overall materiality ({materiality_paise} paise).",
                        how_addressed="Detailed substantive recomputation, management consultation, and ledger verification.",
                        fs_reference="Schedule III Adjustments Note",
                        wp_references=[str(aje.get("id", "WP-AJE"))],
                        is_candidate=True,
                        candidate_source=CandidateKAMSourceEnum.MAJOR_ADJUSTMENT,
                    )
                )

        return candidates

    @staticmethod
    def check_cross_document_consistency(
        fs_revenue_paise: int,
        tb_revenue_paise: int,
        fs_profit_paise: int,
        pnl_profit_paise: int,
        fs_net_worth_paise: int,
        bs_net_worth_paise: int,
        caro_report_answers: dict[str, str],
        caro_workpaper_answers: dict[str, str],
        going_concern_memo_uncertainty: bool,
        fs_has_going_concern_note: bool,
        mrl_signed: bool,
    ) -> list[ConsistencyIssue]:
        """Perform cross-document reconciliation across Financial Statements, Notes, CARO, and MRL."""
        issues: list[ConsistencyIssue] = []

        if fs_revenue_paise != tb_revenue_paise:
            issues.append(
                ConsistencyIssue(
                    category="Financial Statements vs Adjusted TB",
                    field_name="Revenue from Operations",
                    source_a="Financial Statements",
                    value_a=f"{fs_revenue_paise} paise",
                    source_b="Adjusted Trial Balance",
                    value_b=f"{tb_revenue_paise} paise",
                    severity="Critical",
                    explanation="Revenue reported in Schedule III does not reconcile with Adjusted Trial Balance.",
                )
            )

        if fs_profit_paise != pnl_profit_paise:
            issues.append(
                ConsistencyIssue(
                    category="Profit Reconciliation",
                    field_name="Profit for the Period",
                    source_a="Balance Sheet Retained Earnings Delta",
                    value_a=f"{fs_profit_paise} paise",
                    source_b="Statement of Profit and Loss",
                    value_b=f"{pnl_profit_paise} paise",
                    severity="Critical",
                    explanation="Net profit reported in P&L does not reconcile with Balance Sheet surplus movement.",
                )
            )

        if fs_net_worth_paise != bs_net_worth_paise:
            issues.append(
                ConsistencyIssue(
                    category="Net Worth Consistency",
                    field_name="Total Equity / Net Worth",
                    source_a="Ratio Calculation Net Worth",
                    value_a=f"{fs_net_worth_paise} paise",
                    source_b="Balance Sheet Total Equity",
                    value_b=f"{bs_net_worth_paise} paise",
                    severity="Critical",
                    explanation="Disclosed Net Worth diverges from Balance Sheet Share Capital and Reserves.",
                )
            )

        # Check CARO clause divergence
        for clause_code, wp_ans in caro_workpaper_answers.items():
            rep_ans = caro_report_answers.get(clause_code)
            if rep_ans and rep_ans != wp_ans:
                issues.append(
                    ConsistencyIssue(
                        category="CARO 2020 Reporting",
                        field_name=f"Clause {clause_code} Conclusion",
                        source_a="Approved CARO Working Paper",
                        value_a=wp_ans,
                        source_b="Draft CARO Report Text",
                        value_b=rep_ans,
                        severity="Critical",
                        explanation="Draft CARO reporting text diverges from approved clause workpaper conclusion.",
                    )
                )

        # Check Going concern disclosure consistency
        if going_concern_memo_uncertainty and not fs_has_going_concern_note:
            issues.append(
                ConsistencyIssue(
                    category="Going Concern (SA 570)",
                    field_name="Material Uncertainty Disclosure",
                    source_a="SA 570 Going Concern Memo",
                    value_a="Material uncertainty identified",
                    source_b="Financial Statement Notes",
                    value_b="No Note Disclosure Found",
                    severity="Critical",
                    explanation="Material uncertainty on Going Concern was concluded in audit work but is missing from statutory notes.",
                )
            )

        if not mrl_signed:
            issues.append(
                ConsistencyIssue(
                    category="Written Representations (SA 580)",
                    field_name="MRL Execution Status",
                    source_a="Audit Completion Register",
                    value_a="MRL Missing or Unsigned",
                    source_b="Audit Report Sign-off Gate",
                    value_b="Pending Receipt",
                    severity="Critical",
                    explanation="Audit report cannot be finalized without a signed Management Representation Letter.",
                )
            )

        return issues

    @staticmethod
    def calculate_dependency_hash(
        fs_package_hash: str,
        tb_line_count: int,
        total_debit_paise: int,
        total_credit_paise: int,
        caro_conclusions_digest: str,
        going_concern_conclusion: str,
    ) -> str:
        """Generate a deterministic SHA-256 fingerprint of all underlying audit dependencies.

        Used to detect stale audit reports when any underlying source figure or conclusion changes.
        """
        payload = {
            "fs_hash": fs_package_hash,
            "tb_lines": tb_line_count,
            "total_debit": total_debit_paise,
            "total_credit": total_credit_paise,
            "caro_digest": caro_conclusions_digest,
            "gc_conclusion": going_concern_conclusion,
        }
        raw_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
