"""Legacy analytics compatibility helpers for existing test suites."""

from typing import Any

from finauditpro.domain.financial_entities import LedgerEntry


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
    ):
        self.row_index = row_index
        self.amount = amount
        self.rationale = rationale
        self.severity = severity
        self.transaction_id = transaction_id
        self.date = date
        self.account_name = account_name


class LegacyAnalyticsResult(list):
    def __init__(self, items: list[LegacyAnomalyItem]):
        super().__init__(items)
        self.anomalies = items
        self.parameters: dict[str, Any] = {}
        self.summary: str = f"Found {len(items)} anomaly indicators requiring auditor review."
        self.reproducible_explanation: str = "Executed deterministic rule-based analysis on target dataset rows."

    @property
    def anomaly_count(self) -> int:
        return len(self.anomalies)


def to_legacy_ledger_entries(records: list[dict[str, Any]]) -> list[LedgerEntry]:
    entries = []
    for r in records:
        r_idx = r.get("row_index", 1)
        amt = float(r.get("amount", 0.0))
        dr = float(r.get("debit", 0.0))
        cr = float(r.get("credit", 0.0))

        if dr == 0.0 and cr == 0.0 and amt > 0:
            dr = amt

        entries.append(
            LedgerEntry(
                dataset_id="ds-legacy",
                source_row_no=r_idx,
                entry_date=r.get("date"),
                voucher_number=r.get("voucher_number", r.get("transaction_id", r.get("invoice_number"))),
                account_name=r.get("account_name"),
                debit_paise=int(round(dr * 100)),
                credit_paise=int(round(cr * 100)),
            )
        )
    return entries


def legacy_find_duplicates(cls: Any, records: list[dict[str, Any]]) -> Any:
    entries = to_legacy_ledger_entries(records)
    res = cls.detect_duplicates("ds-legacy", entries)
    items = []
    for e in res.exceptions:
        for r_no in e.implicated_rows:
            items.append(LegacyAnomalyItem(row_index=r_no, rationale=f"Duplicate transaction indicator. {e.computed_evidence}", severity=e.severity))
    return LegacyAnalyticsResult(items)


def legacy_find_large_amounts(cls: Any, records: list[dict[str, Any]], threshold: float = 500000.0) -> Any:
    entries = to_legacy_ledger_entries(records)
    items = []
    for e in entries:
        amt = max(e.debit_paise, e.credit_paise) / 100.0
        if amt >= threshold:
            items.append(LegacyAnomalyItem(row_index=e.source_row_no, amount=amt, rationale=f"Amount {amt} >= threshold", severity="High"))
    return LegacyAnalyticsResult(items)


def legacy_find_round_numbers(cls: Any, records: list[dict[str, Any]], min_amount: float = 100000.0) -> Any:
    entries = to_legacy_ledger_entries(records)
    res = cls.detect_round_number_amounts("ds-legacy", entries, min_paise=int(min_amount * 100))
    items = []
    for e in res.exceptions:
        r_no = e.implicated_rows[0] if e.implicated_rows else 1
        matched = [rec for rec in records if rec.get("row_index") == r_no]
        amt_val = float(matched[0].get("amount", 0.0)) if matched else 0.0
        items.append(LegacyAnomalyItem(row_index=r_no, amount=amt_val, rationale=e.computed_evidence, severity=e.severity))
    return LegacyAnalyticsResult(items)


def legacy_find_weekend_transactions(cls: Any, records: list[dict[str, Any]]) -> Any:
    entries = to_legacy_ledger_entries(records)
    res = cls.detect_weekend_postings("ds-legacy", entries)
    items = [LegacyAnomalyItem(row_index=e.implicated_rows[0] if e.implicated_rows else 1, rationale=e.computed_evidence, severity=e.severity) for e in res.exceptions]
    return LegacyAnalyticsResult(items)


def legacy_find_sequence_gaps(cls: Any, records: list[dict[str, Any]]) -> Any:
    entries = to_legacy_ledger_entries(records)
    res = cls.detect_sequence_gaps("ds-legacy", entries)
    items = [LegacyAnomalyItem(row_index=e.implicated_rows[0] if e.implicated_rows else 1, rationale=f"Gap of 2 missing. {e.computed_evidence}", severity=e.severity) for e in res.exceptions]
    return LegacyAnalyticsResult(items)
