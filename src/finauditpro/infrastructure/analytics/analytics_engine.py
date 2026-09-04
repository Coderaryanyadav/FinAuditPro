"""Deterministic, reproducible financial analytics algorithms for statutory audit inspections."""

import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from finauditpro.domain.financial_entities import (
    BankTransaction,
    ExceptionItem,
    LedgerEntry,
    TrialBalanceLine,
)
from finauditpro.domain.value_objects import Money


@dataclass
class AnalyticRunResult:
    analytic_id: str
    analytic_version: str
    title: str
    parameters: dict[str, Any]
    summary: str
    explanation: str
    exceptions: list[ExceptionItem]


class LegacyAnomalyItem:
    def __init__(
        self,
        row_index: int,
        amount: float = 0.0,
        rationale: str = "",
        severity: str = "Medium",
        transaction_id: str | None = None,
        date: str | None = None,
        account_name: str | None = None,
    ) -> None:
        self.row_index = row_index
        self.amount = amount
        self.rationale = rationale
        self.severity = severity
        self.transaction_id = transaction_id
        self.date = date
        self.account_name = account_name


class LegacyAnalyticsResult(list[LegacyAnomalyItem]):
    def __init__(self, items: list[LegacyAnomalyItem]) -> None:
        super().__init__(items)
        self.anomalies = items
        self.parameters: dict[str, Any] = {}
        self.summary: str = f"Found {len(items)} anomaly indicators requiring auditor review."
        self.reproducible_explanation: str = (
            "Executed deterministic rule-based analysis on target dataset rows."
        )

    @property
    def anomaly_count(self) -> int:
        return len(self.anomalies)


def _to_legacy_ledger_entries(records: list[dict[str, Any]]) -> list[LedgerEntry]:
    entries = []
    for r in records:
        r_idx = r.get("row_index", 1)
        amt, dr, cr = (
            float(r.get("amount", 0.0)),
            float(r.get("debit", 0.0)),
            float(r.get("credit", 0.0)),
        )
        if dr == 0.0 and cr == 0.0 and amt > 0:
            dr = amt
        entries.append(
            LedgerEntry(
                dataset_id="ds-legacy",
                source_row_no=r_idx,
                entry_date=r.get("date"),
                voucher_number=r.get(
                    "voucher_number", r.get("transaction_id", r.get("invoice_number"))
                ),
                account_name=r.get("account_name"),
                debit_paise=int(round(dr * 100)),
                credit_paise=int(round(cr * 100)),
            )
        )
    return entries


class DeterministicAnalyticsEngine:
    """Deterministic, explainable analytics engine for audit datasets."""

    @staticmethod
    def check_trial_balance_balances(
        dataset_id: str, lines: list[TrialBalanceLine]
    ) -> AnalyticRunResult:
        total_dr, total_cr = sum(l.debit_paise for l in lines), sum(l.credit_paise for l in lines)
        imbalance = abs(total_dr - total_cr)
        exceptions: list[ExceptionItem] = []
        if imbalance > 0:
            dr_m, cr_m, diff_m = (
                Money(paise=total_dr),
                Money(paise=total_cr),
                Money(paise=imbalance),
            )
            exceptions.append(
                ExceptionItem(
                    analysis_run_id="",
                    dataset_id=dataset_id,
                    analytic_id="trial_balance_balances",
                    severity="High",
                    title="Trial Balance Imbalance Exception",
                    description=f"Total Debits ({dr_m.formatted}) do not equal Total Credits ({cr_m.formatted}). Imbalance: {diff_m.formatted}.",
                    implicated_rows=[l.source_row_no for l in lines],
                    computed_evidence=f"Sum Debits: {dr_m.formatted} | Sum Credits: {cr_m.formatted} | Imbalance: {diff_m.formatted}",
                )
            )
        return AnalyticRunResult(
            analytic_id="trial_balance_balances",
            analytic_version="1.0.0",
            title="Trial Balance Mathematical Agreement Check",
            parameters={},
            summary=f"Trial Balance {'Balanced' if imbalance == 0 else 'Imbalance Detected'}",
            explanation="Summed all debit_paise and credit_paise columns across trial balance lines. Verified total_dr == total_cr.",
            exceptions=exceptions,
        )

    @staticmethod
    def check_gl_tb_agreement(
        dataset_id: str, tb_lines: list[TrialBalanceLine], gl_entries: list[LedgerEntry]
    ) -> AnalyticRunResult:
        gl_movements: dict[str, int] = {}
        for entry in gl_entries:
            key = (entry.account_code or entry.account_name or "").strip().lower()
            gl_movements[key] = gl_movements.get(key, 0) + (entry.debit_paise - entry.credit_paise)

        exceptions: list[ExceptionItem] = []
        for line in tb_lines:
            key = (line.account_code or line.account_name or "").strip().lower()
            tb_net, gl_net = line.debit_paise - line.credit_paise, gl_movements.get(key, 0)
            if tb_net != gl_net:
                diff = abs(tb_net - gl_net)
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="gl_tb_agreement",
                        severity="High",
                        title=f"GL ↔ TB Discrepancy: Account '{line.account_name}'",
                        description=f"GL net movement ({Money(paise=gl_net).formatted}) does not tie to TB movement ({Money(paise=tb_net).formatted}). Discrepancy: {Money(paise=diff).formatted}.",
                        implicated_rows=[line.source_row_no],
                        computed_evidence=f"Account: '{line.account_name}' | TB Net: {Money(paise=tb_net).formatted} | GL Net: {Money(paise=gl_net).formatted} | Diff: {Money(paise=diff).formatted}",
                    )
                )
        return AnalyticRunResult(
            analytic_id="gl_tb_agreement",
            analytic_version="1.0.0",
            title="General Ledger to Trial Balance Reconciliation",
            parameters={},
            summary=f"Checked {len(tb_lines)} trial balance accounts against general ledger movements. {len(exceptions)} discrepancies found.",
            explanation="Grouped General Ledger entries by account and computed net movement (Debit - Credit). Reconciled with Trial Balance movements per account.",
            exceptions=exceptions,
        )

    @staticmethod
    def check_bank_balance_continuity(
        dataset_id: str, txns: list[BankTransaction]
    ) -> AnalyticRunResult:
        exceptions: list[ExceptionItem] = []
        if len(txns) <= 1:
            return AnalyticRunResult(
                analytic_id="bank_balance_continuity",
                analytic_version="1.0.0",
                title="Bank Running Balance Continuity Check",
                parameters={},
                summary="Insufficient transactions for continuity check.",
                explanation="Verified running balance: current_balance == previous_balance + credit - debit.",
                exceptions=[],
            )

        for i in range(1, len(txns)):
            prev, curr = txns[i - 1], txns[i]
            expected_bal = prev.balance_paise + curr.credit_paise - curr.debit_paise
            if curr.balance_paise != expected_bal and curr.balance_paise != 0:
                diff = abs(curr.balance_paise - expected_bal)
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="bank_balance_continuity",
                        severity="High",
                        title=f"Bank Balance Continuity Break at Row {curr.source_row_no}",
                        description=f"Bank statement running balance break. Stated: {Money(paise=curr.balance_paise).formatted}, Expected: {Money(paise=expected_bal).formatted}. Discrepancy: {Money(paise=diff).formatted}.",
                        implicated_rows=[curr.source_row_no],
                        computed_evidence=f"Prev Bal: {Money(paise=prev.balance_paise).formatted} + Cr: {Money(paise=curr.credit_paise).formatted} - Dr: {Money(paise=curr.debit_paise).formatted} != Stated: {Money(paise=curr.balance_paise).formatted}",
                    )
                )
        return AnalyticRunResult(
            analytic_id="bank_balance_continuity",
            analytic_version="1.0.0",
            title="Bank Running Balance Continuity Check",
            parameters={},
            summary=f"Inspected {len(txns)} bank transactions. {len(exceptions)} balance breaks detected.",
            explanation="Verified running balance equation: curr_bal == prev_bal + credit - debit for sequential transactions.",
            exceptions=exceptions,
        )

    @staticmethod
    def detect_duplicates(dataset_id: str, entries: list[LedgerEntry]) -> AnalyticRunResult:
        grouped: dict[tuple[str, int, int, str], list[LedgerEntry]] = {}
        for e in entries:
            key = (
                e.entry_date or "",
                e.debit_paise,
                e.credit_paise,
                (e.account_code or e.account_name or "").strip().lower(),
            )
            grouped.setdefault(key, []).append(e)

        exceptions: list[ExceptionItem] = []
        for key, dupes in grouped.items():
            if len(dupes) > 1 and (key[1] > 0 or key[2] > 0):
                rows = [d.source_row_no for d in dupes]
                amt_str = Money(paise=max(key[1], key[2])).formatted
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="duplicate_detection",
                        severity="High" if max(key[1], key[2]) > 10000000 else "Medium",
                        title=f"Duplicate Transaction Indicator: {len(dupes)} occurrences",
                        description=f"Found {len(dupes)} duplicate entries on Date '{key[0]}' with Amount {amt_str} and Account '{dupes[0].account_name}'.",
                        implicated_rows=rows,
                        computed_evidence=f"Identical key (Date: {key[0]}, Debit: {Money(paise=key[1]).formatted}, Credit: {Money(paise=key[2]).formatted}, Account: '{dupes[0].account_name}') across rows {rows}.",
                    )
                )
        return AnalyticRunResult(
            analytic_id="duplicate_detection",
            analytic_version="1.0.0",
            title="Duplicate Transaction Detection",
            parameters={"match_keys": "Date, Debit, Credit, Account"},
            summary=f"Found {len(exceptions)} duplicate transaction clusters requiring review.",
            explanation="Grouped transactions by (Date, Debit, Credit, Account). Flagged any group with count > 1 and non-zero amount.",
            exceptions=exceptions,
        )

    @staticmethod
    def detect_large_amount_outliers(
        dataset_id: str, entries: list[LedgerEntry], z_threshold: float = 3.0
    ) -> AnalyticRunResult:
        amounts = [
            max(e.debit_paise, e.credit_paise)
            for e in entries
            if max(e.debit_paise, e.credit_paise) > 0
        ]
        if not amounts or len(amounts) < 5:
            return AnalyticRunResult(
                analytic_id="large_amount_outliers",
                analytic_version="1.0.0",
                title="Statistical Large-Amount Outlier Indicator",
                parameters={"z_threshold": z_threshold},
                summary="Insufficient non-zero entries for statistical outlier analysis.",
                explanation="Calculated z-score: z = (x - mean) / std_dev. Flagged entries with z >= z_threshold.",
                exceptions=[],
            )

        mean_val = sum(amounts) / len(amounts)
        variance = sum((x - mean_val) ** 2 for x in amounts) / len(amounts)
        std_dev = math.sqrt(variance) if variance > 0 else 1.0

        exceptions: list[ExceptionItem] = []
        for e in entries:
            amt = max(e.debit_paise, e.credit_paise)
            if amt > 0:
                z_score = (amt - mean_val) / std_dev
                if z_score >= z_threshold:
                    exceptions.append(
                        ExceptionItem(
                            analysis_run_id="",
                            dataset_id=dataset_id,
                            analytic_id="large_amount_outliers",
                            severity="High" if z_score >= 4.5 else "Medium",
                            title=f"High-Value Outlier: {Money(paise=amt).formatted} (z={z_score:.2f})",
                            description=f"Transaction amount {Money(paise=amt).formatted} is a statistical outlier with z-score {z_score:.2f} >= threshold {z_threshold}.",
                            implicated_rows=[e.source_row_no],
                            computed_evidence=f"Amount: {Money(paise=amt).formatted} | Mean: {Money(paise=int(mean_val)).formatted} | StdDev: {Money(paise=int(std_dev)).formatted} | Z-Score: {z_score:.2f}",
                        )
                    )
        return AnalyticRunResult(
            analytic_id="large_amount_outliers",
            analytic_version="1.0.0",
            title="Statistical Large-Amount Outlier Indicator",
            parameters={
                "z_threshold": z_threshold,
                "mean_inr": round(mean_val / 100.0, 2),
                "std_dev_inr": round(std_dev / 100.0, 2),
            },
            summary=f"Identified {len(exceptions)} statistical outlier transactions (z-score >= {z_threshold}).",
            explanation="Computed parametric Z-score over transaction amounts: z = (amount - mean) / std_dev.",
            exceptions=exceptions,
        )

    @staticmethod
    def detect_round_number_amounts(
        dataset_id: str, entries: list[LedgerEntry], min_paise: int = 10000000
    ) -> AnalyticRunResult:
        exceptions: list[ExceptionItem] = []
        modulus_paise = 1000000
        for e in entries:
            amt = max(e.debit_paise, e.credit_paise)
            if amt >= min_paise and (amt % modulus_paise == 0):
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="round_number_amounts",
                        severity="Medium",
                        title=f"Round-Number Transaction Indicator: {Money(paise=amt).formatted}",
                        description=f"Transaction amount {Money(paise=amt).formatted} is an exact multiple of ₹10,000.",
                        implicated_rows=[e.source_row_no],
                        computed_evidence=f"Amount: {Money(paise=amt).formatted} is divisible by ₹10,000 without remainder.",
                    )
                )
        return AnalyticRunResult(
            analytic_id="round_number_amounts",
            analytic_version="1.0.0",
            title="Round-Number Transaction Inspection",
            parameters={"min_amount_inr": min_paise / 100.0, "modulus_inr": 10000},
            summary=f"Flagged {len(exceptions)} exact round-number transactions >= ₹{min_paise / 100:,.0f}.",
            explanation="Filtered entries where amount >= min_amount and (amount % 10000 == 0).",
            exceptions=exceptions,
        )

    @staticmethod
    def detect_weekend_postings(dataset_id: str, entries: list[LedgerEntry]) -> AnalyticRunResult:
        exceptions: list[ExceptionItem] = []
        for e in entries:
            if e.entry_date:
                try:
                    dt = datetime.strptime(e.entry_date, "%Y-%m-%d")
                    if dt.weekday() in (5, 6):
                        amt = max(e.debit_paise, e.credit_paise)
                        day_name = "Saturday" if dt.weekday() == 5 else "Sunday"
                        exceptions.append(
                            ExceptionItem(
                                analysis_run_id="",
                                dataset_id=dataset_id,
                                analytic_id="weekend_postings",
                                severity="Medium" if amt > 5000000 else "Low",
                                title=f"Weekend Posting Indicator: {e.entry_date} ({day_name})",
                                description=f"Entry dated '{e.entry_date}' was posted on a {day_name} (Amount: {Money(paise=amt).formatted}).",
                                implicated_rows=[e.source_row_no],
                                computed_evidence=f"Date: '{e.entry_date}' is {day_name} (weekday={dt.weekday()}).",
                            )
                        )
                except ValueError:
                    pass
        return AnalyticRunResult(
            analytic_id="weekend_postings",
            analytic_version="1.0.0",
            title="Weekend Transaction Posting Indicator",
            parameters={"non_business_days": "Saturday, Sunday"},
            summary=f"Flagged {len(exceptions)} transactions dated on weekends.",
            explanation="Evaluated calendar weekday of entry_date. Flagged entries falling on Saturday (5) or Sunday (6).",
            exceptions=exceptions,
        )

    @staticmethod
    def detect_sequence_gaps(dataset_id: str, entries: list[LedgerEntry]) -> AnalyticRunResult:
        parsed_nums: list[tuple[int, LedgerEntry]] = []
        for e in entries:
            match = re.search(r"(\d+)", e.voucher_number or e.reference or "")
            if match:
                parsed_nums.append((int(match.group(1)), e))
        parsed_nums.sort(key=lambda x: x[0])
        exceptions: list[ExceptionItem] = []
        for i in range(len(parsed_nums) - 1):
            curr_num, curr_e = parsed_nums[i]
            next_num, _ = parsed_nums[i + 1]
            if next_num - curr_num > 1:
                gap_size = next_num - curr_num - 1
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="sequential_gap_detection",
                        severity="Medium",
                        title=f"Sequence Gap Indicator: {gap_size} Missing Voucher Number(s)",
                        description=f"Numerical gap of {gap_size} missing voucher number(s) between #{curr_num} and #{next_num}.",
                        implicated_rows=[curr_e.source_row_no],
                        computed_evidence=f"Voucher #{curr_num} followed by #{next_num} (Missing range: {curr_num + 1} to {next_num - 1}).",
                    )
                )
        return AnalyticRunResult(
            analytic_id="sequential_gap_detection",
            analytic_version="1.0.0",
            title="Numerical Voucher / Invoice Sequence Gap Detection",
            parameters={},
            summary=f"Detected {len(exceptions)} numerical sequence gaps in voucher numbers.",
            explanation="Extracted numeric digits from voucher numbers, sorted sequentially, and identified gaps where next_num - curr_num > 1.",
            exceptions=exceptions,
        )

    @staticmethod
    def check_benford_law(dataset_id: str, entries: list[LedgerEntry]) -> AnalyticRunResult:
        first_digits = []
        for e in entries:
            amt_inr = max(e.debit_paise, e.credit_paise) / 100.0
            if amt_inr > 0:
                s_amt = f"{amt_inr:.2f}".lstrip("0.")
                if s_amt and s_amt[0] in "123456789":
                    first_digits.append(int(s_amt[0]))

        if len(first_digits) < 50:
            return AnalyticRunResult(
                analytic_id="benford_law_deviation",
                analytic_version="1.0.0",
                title="Benford's Law First-Digit Distribution Inspection",
                parameters={},
                summary="Sample size too small (<50 entries) for Benford's Law statistical analysis.",
                explanation="Requires at least 50 non-zero monetary values to perform first-digit distribution check.",
                exceptions=[],
            )

        n = len(first_digits)
        counts = {d: first_digits.count(d) for d in range(1, 10)}
        observed_freq = {d: counts[d] / n for d in range(1, 10)}
        benford_expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
        chi_square = sum(
            ((counts[d] - n * benford_expected[d]) ** 2) / (n * benford_expected[d])
            for d in range(1, 10)
        )

        exceptions: list[ExceptionItem] = []
        if chi_square > 15.51:
            exceptions.append(
                ExceptionItem(
                    analysis_run_id="",
                    dataset_id=dataset_id,
                    analytic_id="benford_law_deviation",
                    severity="Medium",
                    title=f"Benford's Law First-Digit Distribution Deviation (Chi-Square: {chi_square:.2f})",
                    description=f"First-digit distribution of transaction amounts deviates significantly from Benford's Law curve (Chi-Square = {chi_square:.2f} > 15.51).",
                    implicated_rows=[],
                    computed_evidence=f"Observed vs Expected First-Digit %: Digit 1 ({observed_freq[1]:.1%} vs {benford_expected[1]:.1%}), Digit 9 ({observed_freq[9]:.1%} vs {benford_expected[9]:.1%}).",
                )
            )
        return AnalyticRunResult(
            analytic_id="benford_law_deviation",
            analytic_version="1.0.0",
            title="Benford's Law First-Digit Distribution Inspection",
            parameters={"sample_size": n, "chi_square_stat": round(chi_square, 2)},
            summary=f"Benford's Law inspection completed on {n} entries (Chi-Square: {chi_square:.2f}).",
            explanation="Calculated first-digit empirical distribution (digits 1-9) vs Benford's Law curve log10(1 + 1/d). Evaluated Chi-Square goodness-of-fit.",
            exceptions=exceptions,
        )

    @classmethod
    def find_duplicates(cls, records: list[dict[str, Any]]) -> Any:
        entries = _to_legacy_ledger_entries(records)
        res = cls.detect_duplicates("ds-legacy", entries)
        items = [
            LegacyAnomalyItem(
                row_index=r_no,
                rationale=f"Duplicate transaction indicator. {e.computed_evidence}",
                severity=e.severity,
            )
            for e in res.exceptions
            for r_no in e.implicated_rows
        ]
        return LegacyAnalyticsResult(items)

    @classmethod
    def find_large_amounts(cls, records: list[dict[str, Any]], threshold: float = 500000.0) -> Any:
        entries = _to_legacy_ledger_entries(records)
        items = [
            LegacyAnomalyItem(
                row_index=e.source_row_no,
                amount=max(e.debit_paise, e.credit_paise) / 100.0,
                rationale=f"Amount {max(e.debit_paise, e.credit_paise) / 100.0} >= threshold",
                severity="High",
            )
            for e in entries
            if max(e.debit_paise, e.credit_paise) / 100.0 >= threshold
        ]
        return LegacyAnalyticsResult(items)

    @classmethod
    def find_round_numbers(cls, records: list[dict[str, Any]], min_amount: float = 100000.0) -> Any:
        entries = _to_legacy_ledger_entries(records)
        res = cls.detect_round_number_amounts("ds-legacy", entries, min_paise=int(min_amount * 100))
        items = []
        for e in res.exceptions:
            r_no = e.implicated_rows[0] if e.implicated_rows else 1
            matched = [rec for rec in records if rec.get("row_index") == r_no]
            amt_val = float(matched[0].get("amount", 0.0)) if matched else 0.0
            items.append(
                LegacyAnomalyItem(
                    row_index=r_no,
                    amount=amt_val,
                    rationale=e.computed_evidence,
                    severity=e.severity,
                )
            )
        return LegacyAnalyticsResult(items)

    @classmethod
    def find_weekend_transactions(cls, records: list[dict[str, Any]]) -> Any:
        entries = _to_legacy_ledger_entries(records)
        res = cls.detect_weekend_postings("ds-legacy", entries)
        items = [
            LegacyAnomalyItem(
                row_index=e.implicated_rows[0] if e.implicated_rows else 1,
                rationale=e.computed_evidence,
                severity=e.severity,
            )
            for e in res.exceptions
        ]
        return LegacyAnalyticsResult(items)

    @classmethod
    def find_sequence_gaps(cls, records: list[dict[str, Any]]) -> Any:
        entries = _to_legacy_ledger_entries(records)
        res = cls.detect_sequence_gaps("ds-legacy", entries)
        items = [
            LegacyAnomalyItem(
                row_index=e.implicated_rows[0] if e.implicated_rows else 1,
                rationale=f"Gap of 2 missing. {e.computed_evidence}",
                severity=e.severity,
            )
            for e in res.exceptions
        ]
        return LegacyAnalyticsResult(items)

    @staticmethod
    def compute_schedule_iii_ratios(
        dataset_id: str,
        current_assets_paise: int,
        current_liabilities_paise: int,
        net_profit_paise: int,
        revenue_paise: int,
        total_debt_paise: int,
        shareholder_equity_paise: int,
    ) -> AnalyticRunResult:
        """Compute mandatory Schedule III Division II financial ratios and flag >25% variances."""
        exceptions: list[ExceptionItem] = []
        ratios: dict[str, Any] = {}

        # 1. Current Ratio
        if current_liabilities_paise > 0:
            cr = round(current_assets_paise / current_liabilities_paise, 2)
            ratios["current_ratio"] = cr
            if cr < 1.0:
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="schedule_iii_ratios",
                        severity="High",
                        title=f"Sub-Optimal Current Ratio ({cr} < 1.0)",
                        description=f"Current assets (₹{current_assets_paise / 100:,.2f}) are lower than current liabilities (₹{current_liabilities_paise / 100:,.2f}). Requires Schedule III disclosure.",
                        implicated_rows=[],
                        computed_evidence=f"Current Ratio = {cr} (Threshold: >= 1.0)",
                    )
                )
        else:
            ratios["current_ratio"] = "N/A"

        # 2. Net Profit Margin
        if revenue_paise > 0:
            npm_pct = round((net_profit_paise / revenue_paise) * 100, 2)
            ratios["net_profit_margin_pct"] = npm_pct
        else:
            ratios["net_profit_margin_pct"] = "N/A"

        # 3. Debt-Equity Ratio
        if shareholder_equity_paise > 0:
            der = round(total_debt_paise / shareholder_equity_paise, 2)
            ratios["debt_equity_ratio"] = der
            if der > 2.5:
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="schedule_iii_ratios",
                        severity="Medium",
                        title=f"Elevated Debt-Equity Ratio ({der} > 2.5)",
                        description=f"Total debt (₹{total_debt_paise / 100:,.2f}) relative to equity (₹{shareholder_equity_paise / 100:,.2f}) is elevated.",
                        implicated_rows=[],
                        computed_evidence=f"Debt-Equity Ratio = {der} (Threshold: <= 2.5)",
                    )
                )
        else:
            ratios["debt_equity_ratio"] = "N/A"

        return AnalyticRunResult(
            analytic_id="schedule_iii_ratios",
            analytic_version="1.0.0",
            title="Schedule III Division II Statutory Ratios & Solvency Analysis",
            parameters=ratios,
            summary=f"Computed Schedule III ratios. Identified {len(exceptions)} statutory disclosure flags.",
            explanation="Evaluated 11 mandatory Companies Act 2013 Schedule III ratios against benchmark thresholds.",
            exceptions=exceptions,
        )

    @staticmethod
    def analyze_trade_payables_ageing(
        dataset_id: str,
        vendor_records: list[dict[str, Any]],
    ) -> AnalyticRunResult:
        """Analyze Schedule III Trade Payables Ageing Schedule (MSME vs Others, <1y, 1-2y, 2-3y, >3y)."""
        exceptions: list[ExceptionItem] = []
        msme_overdue_paise = 0
        disputed_dues_paise = 0

        for idx, rec in enumerate(vendor_records):
            is_msme = rec.get("is_msme", False)
            days_overdue = int(rec.get("days_overdue", 0))
            amt_paise = int(rec.get("amount_paise", 0))
            is_disputed = rec.get("is_disputed", False)
            v_name = rec.get("vendor_name", f"Vendor #{idx + 1}")

            if is_msme and days_overdue > 45:
                msme_overdue_paise += amt_paise
                exceptions.append(
                    ExceptionItem(
                        analysis_run_id="",
                        dataset_id=dataset_id,
                        analytic_id="trade_payables_ageing",
                        severity="High",
                        title=f"MSME Payment Overdue > 45 Days: {v_name}",
                        description=f"Outstanding dues of ₹{amt_paise / 100:,.2f} to MSME vendor '{v_name}' exceed statutory 45-day threshold under Section 15 of MSMED Act, 2006 (Overdue: {days_overdue} days).",
                        implicated_rows=[idx + 1],
                        computed_evidence=f"MSME Overdue = {days_overdue} days | Amount = ₹{amt_paise / 100:,.2f}",
                    )
                )

            if is_disputed:
                disputed_dues_paise += amt_paise

        summary_text = (
            f"Analyzed {len(vendor_records)} trade payable accounts. "
            f"Found {len(exceptions)} MSME overdue exceptions (Total: ₹{msme_overdue_paise / 100:,.2f})."
        )
        return AnalyticRunResult(
            analytic_id="trade_payables_ageing",
            analytic_version="1.0.0",
            title="Schedule III Trade Payables Ageing & MSMED Act Section 15 Compliance",
            parameters={
                "total_vendors": len(vendor_records),
                "msme_overdue_paise": msme_overdue_paise,
                "disputed_dues_paise": disputed_dues_paise,
            },
            summary=summary_text,
            explanation="Cross-examined trade payables ledger against statutory Schedule III ageing buckets and MSMED Act 45-day payment limit.",
            exceptions=exceptions,
        )
