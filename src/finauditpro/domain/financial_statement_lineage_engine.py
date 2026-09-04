"""Pure domain extraction engine for Financial Statement Data Lineage."""

from typing import Any

from finauditpro.domain.financial_statement_entities import (
    BalanceSheet,
    DataLineageNode,
    FinancialStatementNote,
    ProfitAndLossStatement,
)


def extract_data_lineage_trace(
    fs_line_code: str,
    bs: BalanceSheet,
    pnl: ProfitAndLossStatement,
    notes: list[FinancialStatementNote],
    adjusted_tb_lines: list[Any],
) -> DataLineageNode:
    """Extract complete deterministic lineage: FS Line -> Note -> Mapped Accounts -> Adjusted TB -> AJE -> Original TB."""
    line_item = None
    for l in bs.equity_and_liabilities_lines + bs.assets_lines:
        if l.line_code == fs_line_code:
            line_item = l
            break
    if not line_item:
        for l in pnl.revenue_lines + pnl.expense_lines:
            if l.line_code == fs_line_code:
                line_item = l
                break

    if not line_item:
        return DataLineageNode(
            fs_line_code=fs_line_code,
            fs_line_name="Unknown Line Item",
            total_amount_paise=0,
        )

    matched_note = next((n for n in notes if n.note_number == line_item.note_ref), None)

    traces = []
    for code in line_item.mapped_account_codes:
        tb_line = next((t for t in adjusted_tb_lines if t.account_code == code), None)
        if tb_line:
            traces.append(
                {
                    "account_code": tb_line.account_code,
                    "account_name": tb_line.account_name,
                    "unadjusted_net_paise": tb_line.unadjusted_net_paise,
                    "net_adjustment_paise": tb_line.net_adjustment_paise,
                    "adjusted_net_paise": tb_line.adjusted_net_paise,
                    "linked_aje_numbers": getattr(tb_line, "linked_aje_numbers", []),
                }
            )

    return DataLineageNode(
        fs_line_code=line_item.line_code,
        fs_line_name=line_item.category,
        note_ref=line_item.note_ref,
        note_title=matched_note.title if matched_note else None,
        total_amount_paise=line_item.current_period_paise,
        account_traces=traces,
    )
