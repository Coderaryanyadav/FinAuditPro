"""Pure domain evaluation engine for Indirect Cash Flow Statement and Changes in Equity."""

from finauditpro.domain.financial_statement_entities import (
    BalanceSheet,
    CashFlowActivityTypeEnum,
    CashFlowLineItem,
    CashFlowStatement,
    ProfitAndLossStatement,
    StatementOfChangesInEquity,
)


def build_statement_of_changes_in_equity(
    engagement_id: str,
    bs: BalanceSheet,
    pnl: ProfitAndLossStatement,
) -> StatementOfChangesInEquity:
    """Derive Statement of Changes in Equity linking opening, PAT, and closing balances."""
    share_cap = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Share Capital"
        ),
        0,
    )
    reserves = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Reserves and Surplus"
        ),
        0,
    )
    pat = pnl.profit_after_tax_paise

    return StatementOfChangesInEquity(
        engagement_id=engagement_id,
        opening_share_capital_paise=share_cap,
        share_capital_changes_paise=0,
        closing_share_capital_paise=share_cap,
        opening_reserves_surplus_paise=(
            reserves - pat if reserves >= pat else reserves
        ),
        profit_for_the_year_paise=pat,
        dividends_paid_paise=0,
        transfers_paise=0,
        closing_reserves_surplus_paise=reserves,
        total_closing_equity_paise=share_cap + reserves,
    )


def build_indirect_cash_flow_statement(
    engagement_id: str,
    for_period_ended: str,
    bs: BalanceSheet,
    pnl: ProfitAndLossStatement,
) -> CashFlowStatement:
    """Generate Indirect Method Cash Flow Statement with strict Cash reconciliation invariants."""
    pbt = pnl.profit_before_tax_paise
    depr = next(
        (
            l.current_period_paise
            for l in pnl.expense_lines
            if l.category == "Depreciation and Amortization"
        ),
        0,
    )
    fin_cost = next(
        (
            l.current_period_paise
            for l in pnl.expense_lines
            if l.category == "Finance Costs"
        ),
        0,
    )

    # Working Capital Changes from Balance Sheet
    inv_amt = next(
        (l.current_period_paise for l in bs.assets_lines if l.category == "Inventories"),
        0,
    )
    rec_amt = next(
        (
            l.current_period_paise
            for l in bs.assets_lines
            if l.category == "Trade Receivables"
        ),
        0,
    )
    pay_amt = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Trade Payables"
        ),
        0,
    )
    other_cur_liab = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Other Current Liabilities"
        ),
        0,
    )

    # Operating Activities
    op_lines = [
        CashFlowLineItem(
            description="Profit Before Tax (PBT)",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=pbt,
        ),
        CashFlowLineItem(
            description="Adjustment for Non-Cash Depreciation",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=depr,
        ),
        CashFlowLineItem(
            description="Adjustment for Finance Costs",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=fin_cost,
        ),
        CashFlowLineItem(
            description="Operating Cash Before Working Capital Changes",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=pbt + depr + fin_cost,
        ),
        CashFlowLineItem(
            description="(Increase) / Decrease in Inventories",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=-inv_amt,
        ),
        CashFlowLineItem(
            description="(Increase) / Decrease in Trade Receivables",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=-rec_amt,
        ),
        CashFlowLineItem(
            description="Increase / (Decrease) in Trade Payables",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=pay_amt,
        ),
        CashFlowLineItem(
            description="Increase / (Decrease) in Other Current Liabilities",
            activity_type=CashFlowActivityTypeEnum.OPERATING,
            amount_paise=other_cur_liab,
        ),
    ]
    net_op = (
        (pbt + depr + fin_cost) - inv_amt - rec_amt + pay_amt + other_cur_liab
    )

    # Investing Activities
    ppe_amt = next(
        (
            l.current_period_paise
            for l in bs.assets_lines
            if l.category == "Property, Plant and Equipment"
        ),
        0,
    )
    # Gross capital expenditure (Net PPE + non-cash depreciation charged)
    capex = ppe_amt + depr if ppe_amt > 0 else 0
    inv_lines = [
        CashFlowLineItem(
            description="Purchase of Property, Plant & Equipment / Capital Expenditure",
            activity_type=CashFlowActivityTypeEnum.INVESTING,
            amount_paise=-capex,
            is_inflow=False,
        ),
    ]
    net_inv = -capex

    # Financing Activities
    share_cap = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Share Capital"
        ),
        0,
    )
    reserves_amt = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Reserves and Surplus"
        ),
        0,
    )
    opening_reserves = (
        reserves_amt - pnl.profit_after_tax_paise
        if reserves_amt >= pnl.profit_after_tax_paise
        else 0
    )
    borrowing_amt = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Long-Term Borrowings"
        ),
        0,
    )
    st_borrow_amt = next(
        (
            l.current_period_paise
            for l in bs.equity_and_liabilities_lines
            if l.category == "Short-Term Borrowings"
        ),
        0,
    )
    fin_lines = []
    if share_cap > 0:
        fin_lines.append(
            CashFlowLineItem(
                description="Proceeds from Issue of Share Capital",
                activity_type=CashFlowActivityTypeEnum.FINANCING,
                amount_paise=share_cap,
                is_inflow=True,
            )
        )
    if opening_reserves > 0:
        fin_lines.append(
            CashFlowLineItem(
                description="Opening Capital & Reserves Movement",
                activity_type=CashFlowActivityTypeEnum.FINANCING,
                amount_paise=opening_reserves,
                is_inflow=True,
            )
        )
    if borrowing_amt != 0:
        fin_lines.append(
            CashFlowLineItem(
                description="Proceeds from / (Repayment of) Long-Term Borrowings",
                activity_type=CashFlowActivityTypeEnum.FINANCING,
                amount_paise=borrowing_amt,
                is_inflow=borrowing_amt > 0,
            )
        )
    if st_borrow_amt != 0:
        fin_lines.append(
            CashFlowLineItem(
                description="Proceeds from / (Repayment of) Short-Term Bank Borrowings",
                activity_type=CashFlowActivityTypeEnum.FINANCING,
                amount_paise=st_borrow_amt,
                is_inflow=st_borrow_amt > 0,
            )
        )
    if fin_cost > 0:
        fin_lines.append(
            CashFlowLineItem(
                description="Finance Costs Paid",
                activity_type=CashFlowActivityTypeEnum.FINANCING,
                amount_paise=-fin_cost,
                is_inflow=False,
            )
        )
    net_fin = share_cap + opening_reserves + borrowing_amt + st_borrow_amt - fin_cost

    net_change = net_op + net_inv + net_fin

    # Cash Reconciliation
    fs_cash = next(
        (
            l.current_period_paise
            for l in bs.assets_lines
            if l.category == "Cash and Cash Equivalents"
        ),
        0,
    )
    opening_cash = 0
    closing_cash = opening_cash + net_change
    diff = fs_cash - closing_cash
    is_reconciled = bool(diff == 0)

    return CashFlowStatement(
        engagement_id=engagement_id,
        for_period_ended=for_period_ended,
        operating_activities=op_lines,
        investing_activities=inv_lines,
        financing_activities=fin_lines,
        net_cash_from_operating_paise=net_op,
        net_cash_from_investing_paise=net_inv,
        net_cash_from_financing_paise=net_fin,
        net_increase_in_cash_paise=net_change,
        opening_cash_and_equivalents_paise=opening_cash,
        closing_cash_and_equivalents_paise=closing_cash,
        financial_statement_cash_balance_paise=fs_cash,
        is_reconciled=is_reconciled,
        reconciliation_difference_paise=diff,
    )
