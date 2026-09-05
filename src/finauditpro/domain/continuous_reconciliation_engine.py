"""Continuous reconciliation and materiality exposure monitoring engine."""

from dataclasses import dataclass
from typing import Any

from finauditpro.domain.continuous_audit_entities import (
    ContinuousReconciliationResult,
)


@dataclass
class ContinuousMaterialityExposure:
    benchmark_name: str
    overall_materiality_paise: int
    performance_materiality_paise: int
    clearly_trivial_threshold_paise: int
    known_misstatement_paise: int
    potential_risk_exposure_paise: int
    remaining_overall_headroom_paise: int
    remaining_perf_headroom_paise: int
    is_overall_materiality_breached: bool
    is_perf_materiality_breached: bool
    notes: str


class ContinuousReconciliationEngine:
    """Continuously verifies ledger balancing, subledger reconciliations, and materiality headroom."""

    def reconcile_trial_balance(
        self,
        tb_lines: list[dict[str, Any]],
        tolerance_paise: int = 0,
    ) -> ContinuousReconciliationResult:
        """Verifies total debits equal total credits across trial balance accounts."""
        tot_dr = sum(int(line.get("debit_paise") or line.get("closing_dr_paise") or 0) for line in tb_lines)
        tot_cr = sum(int(line.get("credit_paise") or line.get("closing_cr_paise") or 0) for line in tb_lines)
        diff = abs(tot_dr - tot_cr)

        status = "BALANCED" if diff <= tolerance_paise else "DISCREPANCY"
        details = (
            f"Trial balance is mathematically balanced (Total Dr = ₹{tot_dr / 100:,.2f}, Total Cr = ₹{tot_cr / 100:,.2f})."
            if status == "BALANCED"
            else f"Trial balance out of balance by ₹{diff / 100:,.2f} (Total Dr = ₹{tot_dr / 100:,.2f}, Total Cr = ₹{tot_cr / 100:,.2f})."
        )

        return ContinuousReconciliationResult(
            reconciliation_type="TB_BALANCE",
            expected_paise=tot_dr,
            actual_paise=tot_cr,
            difference_paise=diff,
            threshold_paise=tolerance_paise,
            status=status,
            details=details,
        )

    def reconcile_subledger_to_gl(
        self,
        subledger_name: str,
        gl_account_balance_paise: int,
        subledger_total_paise: int,
        tolerance_paise: int = 100,  # ₹1.00 tolerance for rounding
    ) -> ContinuousReconciliationResult:
        """Verifies control accounts in General Ledger against detailed subledger listings."""
        diff = abs(gl_account_balance_paise - subledger_total_paise)
        status = "BALANCED" if diff <= tolerance_paise else "DISCREPANCY"
        details = (
            f"{subledger_name} subledger reconciles with GL control account (Diff: ₹{diff / 100:,.2f})."
            if status == "BALANCED"
            else f"Reconciliation break on {subledger_name}: GL control account ₹{gl_account_balance_paise / 100:,.2f} differs from subledger listing ₹{subledger_total_paise / 100:,.2f} by ₹{diff / 100:,.2f}."
        )

        return ContinuousReconciliationResult(
            reconciliation_type=f"SUBLEDGER_{subledger_name.upper()}_VS_GL",
            expected_paise=gl_account_balance_paise,
            actual_paise=subledger_total_paise,
            difference_paise=diff,
            threshold_paise=tolerance_paise,
            status=status,
            details=details,
        )

    def evaluate_materiality_exposure(
        self,
        overall_materiality_paise: int,
        performance_materiality_paise: int,
        clearly_trivial_threshold_paise: int,
        known_misstatements_paise: int,
        unreviewed_alerts_aggregate_paise: int,
    ) -> ContinuousMaterialityExposure:
        """Tracks potential and known exposure against materiality parameters."""
        rem_overall = overall_materiality_paise - (known_misstatements_paise + unreviewed_alerts_aggregate_paise)
        rem_perf = performance_materiality_paise - (known_misstatements_paise + unreviewed_alerts_aggregate_paise)

        breached_overall = rem_overall < 0
        breached_perf = rem_perf < 0

        notes = (
            "Cumulative unreviewed potential risk exposure exceeds performance materiality. "
            "Requires immediate substantive testing prioritization."
            if breached_perf
            else "Materiality headroom is adequate. Emerging risk items remain within manageable audit thresholds."
        )

        return ContinuousMaterialityExposure(
            benchmark_name="SA 320 Dynamic Materiality Tracker",
            overall_materiality_paise=overall_materiality_paise,
            performance_materiality_paise=performance_materiality_paise,
            clearly_trivial_threshold_paise=clearly_trivial_threshold_paise,
            known_misstatement_paise=known_misstatements_paise,
            potential_risk_exposure_paise=unreviewed_alerts_aggregate_paise,
            remaining_overall_headroom_paise=rem_overall,
            remaining_perf_headroom_paise=rem_perf,
            is_overall_materiality_breached=breached_overall,
            is_perf_materiality_breached=breached_perf,
            notes=notes,
        )
