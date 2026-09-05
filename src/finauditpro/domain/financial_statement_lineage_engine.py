"""Pure domain extraction engine for Financial Statement Data Lineage."""

from typing import Any

from finauditpro.domain.financial_statement_entities import (
    BalanceSheet,
    BalanceSheetLineItem,
    DataLineageNode,
    FinancialStatementNote,
    ProfitAndLossLineItem,
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
    target_line: BalanceSheetLineItem | ProfitAndLossLineItem | None = None

    for bsl in bs.equity_and_liabilities_lines + bs.assets_lines:
        if bsl.line_code == fs_line_code:
            target_line = bsl
            break

    if target_line is None:
        for pnll in pnl.revenue_lines + pnl.expense_lines:
            if pnll.line_code == fs_line_code:
                target_line = pnll
                break

    if target_line is None:
        return DataLineageNode(
            fs_line_code=fs_line_code,
            fs_line_name="Unknown Line Item",
            total_amount_paise=0,
        )

    matched_note = next((n for n in notes if n.note_number == target_line.note_ref), None)

    traces = []
    for code in target_line.mapped_account_codes:
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
        fs_line_code=target_line.line_code,
        fs_line_name=target_line.category,
        note_ref=target_line.note_ref,
        note_title=matched_note.title if matched_note else None,
        total_amount_paise=target_line.current_period_paise,
        account_traces=traces,
    )

