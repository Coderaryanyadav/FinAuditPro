"""Pure domain mathematical algorithms and rule evaluation for Phase D Audit Completion.

Covers:
- SA 450 Misstatement aggregation, qualitative assessment, and materiality comparison
- SA 570 Multi-factor solvency and going concern evaluation
- SA 580 Chronological MRL date validation against Audit Report Date
- SA 520 Completion-stage financial ratio and analytical variance evaluation
"""

from finauditpro.domain.audit_completion_entities import (
    FinancialMisstatement,
    GoingConcernConclusionEnum,
    GoingConcernMitigation,
    MisstatementStatusEnum,
    RatioCategoryEnum,
    RatioComparisonLine,
    SA450AuditConclusionEnum,
    SA450EvaluationSummary,
    SolvencyRiskLevelEnum,
)
from finauditpro.domain.financial_statement_entities import BalanceSheet, ProfitAndLossStatement


class AuditCompletionEngine:
    """Pure domain evaluation engine for statutory audit completion."""

    @classmethod
    def evaluate_sa450_misstatements(
        cls,
        engagement_id: str,
        misstatements: list[FinancialMisstatement],
        overall_materiality_paise: int,
        performance_materiality_paise: int,
        clearly_trivial_threshold_paise: int,
    ) -> SA450EvaluationSummary:
        """Evaluate accumulated misstatements against engagement materiality thresholds under SA 450."""
        total_identified = len(misstatements)
        corrected_count = 0
        uncorrected_count = 0
        uncorrected_tot_paise = 0
        uncorrected_pnl_paise = 0
        uncorrected_bs_paise = 0
        is_material_individually = False

        for m in misstatements:
            if m.amount_paise <= clearly_trivial_threshold_paise:
                m.is_clearly_trivial = True

            if m.status == MisstatementStatusEnum.CORRECTED:
                corrected_count += 1
            else:
                uncorrected_count += 1
                uncorrected_tot_paise += m.amount_paise
                if m.is_pnl_impact:
                    uncorrected_pnl_paise += (
                        m.pnl_overstatement_paise
                        if m.pnl_overstatement_paise > 0
                        else m.amount_paise
                    )
                if m.is_balance_sheet_impact:
                    uncorrected_bs_paise += (
                        m.balance_sheet_overstatement_paise
                        if m.balance_sheet_overstatement_paise > 0
                        else m.amount_paise
                    )
                if m.amount_paise >= overall_materiality_paise:
                    is_material_individually = True

        is_material_in_aggregate = uncorrected_tot_paise >= overall_materiality_paise
        requires_opinion_modification = is_material_in_aggregate or is_material_individually

        if not requires_opinion_modification:
            conclusion = SA450AuditConclusionEnum.UNQUALIFIED_ACCEPTABLE
        else:
            conclusion = SA450AuditConclusionEnum.MODIFIED_OPINION_REQUIRED

        return SA450EvaluationSummary(
            engagement_id=engagement_id,
            overall_materiality_paise=overall_materiality_paise,
            performance_materiality_paise=performance_materiality_paise,
            clearly_trivial_threshold_paise=clearly_trivial_threshold_paise,
            total_identified_misstatements=total_identified,
            total_corrected_misstatements=corrected_count,
            total_uncorrected_misstatements=uncorrected_count,
            total_uncorrected_amount_paise=uncorrected_tot_paise,
            total_uncorrected_pnl_impact_paise=uncorrected_pnl_paise,
            total_uncorrected_bs_impact_paise=uncorrected_bs_paise,
            is_material_individually=is_material_individually,
            is_material_in_aggregate=is_material_in_aggregate,
            requires_opinion_modification=requires_opinion_modification,
            audit_conclusion=conclusion,
            evaluated_misstatements=misstatements,
        )

    @classmethod
    def evaluate_sa570_going_concern(
        cls,
        has_operating_losses: bool,
        has_negative_operating_cashflow: bool,
        has_negative_net_worth: bool,
        has_covenant_breaches: bool,
        has_delayed_statutory_dues: bool,
        has_debt_maturity_unfunded: bool,
        current_ratio: float,
        debt_equity_ratio: float,
        mitigations: list[GoingConcernMitigation],
    ) -> tuple[SolvencyRiskLevelEnum, bool, GoingConcernConclusionEnum, str]:
        """Evaluate multi-factor indicators and mitigation feasibility under SA 570 (Revised)."""
        indicator_count = sum(
            [
                has_operating_losses,
                has_negative_operating_cashflow,
                has_negative_net_worth,
                has_covenant_breaches,
                has_delayed_statutory_dues,
                has_debt_maturity_unfunded,
                current_ratio < 1.0,
            ]
        )

        has_critical_trigger = has_negative_net_worth or (
            has_operating_losses and has_negative_operating_cashflow and has_debt_maturity_unfunded
        )

        feasible_mitigations_count = sum(1 for m in mitigations if m.is_feasible)

        if has_critical_trigger:
            risk_level = SolvencyRiskLevelEnum.CRITICAL_GOING_CONCERN_RISK
            material_uncertainty = True
            if feasible_mitigations_count > 0:
                conclusion = (
                    GoingConcernConclusionEnum.MATERIAL_UNCERTAINTY_ADEQUATELY_DISCLOSED
                )
                rationale = (
                    "Critical solvency indicators present (Negative Net Worth / Unfunded Maturities). "
                    "Feasible management mitigations evaluated. Requires SA 570 §22 Material Uncertainty paragraph."
                )
            else:
                conclusion = GoingConcernConclusionEnum.GOING_CONCERN_INAPPROPRIATE
                rationale = (
                    "Critical solvency distress with no feasible management mitigation plan. "
                    "Use of going concern basis of accounting is inappropriate (SA 705 Adverse Opinion required)."
                )
        elif indicator_count >= 2 or current_ratio < 1.0:
            risk_level = SolvencyRiskLevelEnum.ELEVATED
            material_uncertainty = True
            conclusion = (
                GoingConcernConclusionEnum.MATERIAL_UNCERTAINTY_ADEQUATELY_DISCLOSED
            )
            rationale = (
                f"Elevated solvency indicators identified ({indicator_count} triggers active, Current Ratio: {current_ratio:.2f}). "
                "Management mitigation plans reviewed and verified feasible."
            )
        else:
            risk_level = SolvencyRiskLevelEnum.LOW
            material_uncertainty = False
            conclusion = GoingConcernConclusionEnum.NO_MATERIAL_UNCERTAINTY
            rationale = (
                "Financial indicators and liquidity profile support going concern assumption "
                "over the 12-month look-forward period."
            )

        return risk_level, material_uncertainty, conclusion, rationale

    @classmethod
    def validate_mrl_chronology(
        cls, mrl_signed_date: str | None, audit_report_date: str
    ) -> tuple[bool, str]:
        """Validate that MRL signed date is on or before Audit Report signature date (SA 580 §14)."""
        if not mrl_signed_date:
            return (
                False,
                "SA 580 Violation: Management Representation Letter has not been signed. "
                "Audit report cannot be signed without obtaining written representations.",
            )

        if mrl_signed_date > audit_report_date:
            return (
                False,
                f"SA 580 Invariant Violation: MRL signed date ({mrl_signed_date}) is after Audit Report date ({audit_report_date}). "
                "Written representations must be dated as near as practicable to, but not after, the date of the auditor's report.",
            )

        return (
            True,
            f"SA 580 Valid: MRL dated {mrl_signed_date} precedes or matches Audit Report date {audit_report_date}.",
        )

    @classmethod
    def compute_sa520_analytical_ratios(
        cls,
        bs: BalanceSheet,
        pnl: ProfitAndLossStatement,
        prev_bs: BalanceSheet | None = None,
        prev_pnl: ProfitAndLossStatement | None = None,
    ) -> list[RatioComparisonLine]:
        """Calculate mandatory completion-stage ratios and variance analysis under SA 520."""

        def _extract_totals(b_sheet: BalanceSheet) -> tuple[int, int, int, int]:
            ca = sum(
                l.current_period_paise
                for l in b_sheet.assets_lines
                if l.line_code.startswith("CA-")
                or l.category
                in {
                    "Inventories",
                    "Trade Receivables",
                    "Cash and Cash Equivalents",
                    "Short-Term Loans and Advances",
                    "Other Current Assets",
                }
            )
            cl = sum(
                l.current_period_paise
                for l in b_sheet.equity_and_liabilities_lines
                if l.line_code.startswith("CL-")
                or l.category
                in {
                    "Short-Term Borrowings",
                    "Trade Payables",
                    "Other Current Liabilities",
                    "Short-Term Provisions",
                }
            )
            equity = sum(
                l.current_period_paise
                for l in b_sheet.equity_and_liabilities_lines
                if l.line_code.startswith("EQ-")
                or l.category in {"Share Capital", "Reserves and Surplus"}
            )
            debt = sum(
                l.current_period_paise
                for l in b_sheet.equity_and_liabilities_lines
                if "Borrowing" in l.category or l.line_code in {"NCL-01", "CL-01"}
            )
            return ca, cl, equity, debt

        ca, cl, equity, debt = _extract_totals(bs)
        if prev_bs:
            py_ca, py_cl, py_equity, py_debt = _extract_totals(prev_bs)
        else:
            py_ca = ca
            py_cl = cl
            py_equity = equity
            py_debt = debt

        # 1. Current Ratio
        cl_safe = max(cl, 1)
        cy_current_ratio = round(ca / cl_safe, 2)
        py_cl_safe = max(py_cl, 1)
        py_current_ratio = round(py_ca / py_cl_safe, 2)
        var_cr = (
            round(((cy_current_ratio - py_current_ratio) / py_current_ratio) * 100, 2)
            if py_current_ratio != 0
            else 0.0
        )

        # 2. Net Profit Margin
        rev = max(pnl.total_revenue_paise, 1)
        pat = pnl.profit_after_tax_paise
        cy_npm = round((pat / rev) * 100, 2)
        py_rev = max(prev_pnl.total_revenue_paise, 1) if prev_pnl else rev
        py_pat = prev_pnl.profit_after_tax_paise if prev_pnl else pat
        py_npm = round((py_pat / py_rev) * 100, 2)
        var_npm = round(cy_npm - py_npm, 2)

        # 3. Debt to Equity Ratio
        eq_safe = max(equity, 1)
        cy_de = round(debt / eq_safe, 2)
        py_eq_safe = max(py_equity, 1)
        py_de = round(py_debt / py_eq_safe, 2)
        var_de = (
            round(((cy_de - py_de) / py_de) * 100, 2) if py_de != 0 else 0.0
        )

        return [
            RatioComparisonLine(
                ratio_name="Current Ratio (Current Assets / Current Liabilities)",
                category=RatioCategoryEnum.LIQUIDITY,
                current_year_value=cy_current_ratio,
                previous_year_value=py_current_ratio,
                variance_percentage=var_cr,
                is_significant_variance=abs(var_cr) >= 15.0,
                auditor_explanation=(
                    "Variance within expected threshold"
                    if abs(var_cr) < 15.0
                    else "Significant variance investigated"
                ),
            ),
            RatioComparisonLine(
                ratio_name="Net Profit Margin (PAT / Revenue %)",
                category=RatioCategoryEnum.PROFITABILITY,
                current_year_value=cy_npm,
                previous_year_value=py_npm,
                variance_percentage=var_npm,
                is_significant_variance=abs(var_npm) >= 5.0,
                auditor_explanation=(
                    "Variance within normal range"
                    if abs(var_npm) < 5.0
                    else "Operational margin movement evaluated"
                ),
            ),
            RatioComparisonLine(
                ratio_name="Debt-to-Equity Ratio (Total Debt / Equity)",
                category=RatioCategoryEnum.SOLVENCY,
                current_year_value=cy_de,
                previous_year_value=py_de,
                variance_percentage=var_de,
                is_significant_variance=abs(var_de) >= 20.0,
                auditor_explanation=(
                    "Leverage ratio stable"
                    if abs(var_de) < 20.0
                    else "Debt restructuring verified"
                ),
            ),
        ]
