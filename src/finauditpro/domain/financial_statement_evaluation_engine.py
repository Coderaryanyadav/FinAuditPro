"""Pure domain evaluation engines for Schedule III Financial Statements, Cash Flow, and Data Lineage."""

from collections import defaultdict
from typing import Any

from finauditpro.domain.financial_statement_entities import (
    BalanceSheet,
    BalanceSheetLineItem,
    ProfitAndLossLineItem,
    ProfitAndLossStatement,
    ScheduleIIIDivisionEnum,
    ScheduleIIISectionEnum,
)


def build_schedule_iii_balance_sheet(
    engagement_id: str,
    as_at_date: str,
    adjusted_tb_lines: list[Any],
    division: ScheduleIIIDivisionEnum = ScheduleIIIDivisionEnum.DIVISION_I_AS,
) -> BalanceSheet:
    """Construct Schedule III Balance Sheet from Adjusted Trial Balance lines."""
    cat_accounts: dict[str, list[Any]] = defaultdict(list)
    cat_net: dict[str, int] = defaultdict(int)
    unmapped: list[str] = []

    for line in adjusted_tb_lines:
        cat = getattr(line, "schedule_iii_category", "") or ""
        if not cat:
            unmapped.append(line.account_code)
            continue
        cat_accounts[cat].append(line)
        cat_net[cat] += line.adjusted_net_paise

    # Equity & Liabilities Categories
    eq_liab_specs = [
        ("EQ-01", "Share Capital", "Equity Share Capital", "Note 1"),
        ("EQ-02", "Reserves and Surplus", "Retained Earnings / Reserves", "Note 2"),
        ("NCL-01", "Long-Term Borrowings", "Term Loans & Borrowings", "Note 3"),
        ("NCL-02", "Deferred Tax Liabilities (Net)", "Deferred Tax Liabilities", "Note 4"),
        ("NCL-03", "Other Long-Term Liabilities", "Trade & Security Deposits", "Note 5"),
        ("CL-01", "Short-Term Borrowings", "Working Capital Overdrafts", "Note 6"),
        ("CL-02", "Trade Payables", "Trade Payables (MSME & Others)", "Note 7"),
        ("CL-03", "Other Current Liabilities", "Statutory Dues & Advances", "Note 8"),
        ("CL-04", "Short-Term Provisions", "Provisions for Tax & Expenses", "Note 9"),
    ]

    eq_lines: list[BalanceSheetLineItem] = []
    tot_eq_liab = 0
    for code, cat, desc, nref in eq_liab_specs:
        accs = cat_accounts.get(cat, [])
        # Liabilities/Equity have normal credit balance (credit net is -adjusted_net)
        amt = -sum(a.adjusted_net_paise for a in accs) if accs else 0
        tot_eq_liab += amt
        eq_lines.append(
            BalanceSheetLineItem(
                line_code=code,
                section=ScheduleIIISectionEnum.EQUITY_AND_LIABILITIES,
                category=cat,
                line_item=desc,
                current_period_paise=amt,
                note_ref=nref,
                mapped_account_codes=[a.account_code for a in accs],
            )
        )

    # Assets Categories
    asset_specs = [
        ("NCA-01", "Property, Plant and Equipment", "Tangible Fixed Assets", "Note 10"),
        ("NCA-02", "Capital Work-in-Progress (CWIP)", "Capital Work in Progress", "Note 11"),
        ("NCA-03", "Intangible Assets", "Software & Patents", "Note 12"),
        ("NCA-04", "Non-Current Investments", "Investments in Shares & Bonds", "Note 13"),
        ("NCA-05", "Long-Term Loans and Advances", "Security Deposits & Advances", "Note 14"),
        ("CA-01", "Inventories", "Inventories (Stock in Trade)", "Note 15"),
        ("CA-02", "Trade Receivables", "Trade Debtors (Undisputed)", "Note 16"),
        ("CA-03", "Cash and Cash Equivalents", "Bank Balances & Cash", "Note 17"),
        ("CA-04", "Short-Term Loans and Advances", "GST / Advance Tax / Prepaids", "Note 18"),
        ("CA-05", "Other Current Assets", "Interest Accrued & Others", "Note 19"),
    ]

    asset_lines: list[BalanceSheetLineItem] = []
    tot_assets = 0
    for code, cat, desc, nref in asset_specs:
        accs = cat_accounts.get(cat, [])
        amt = sum(a.adjusted_net_paise for a in accs) if accs else 0
        tot_assets += amt
        asset_lines.append(
            BalanceSheetLineItem(
                line_code=code,
                section=ScheduleIIISectionEnum.ASSETS,
                category=cat,
                line_item=desc,
                current_period_paise=amt,
                note_ref=nref,
                mapped_account_codes=[a.account_code for a in accs],
            )
        )

    diff = tot_assets - tot_eq_liab
    is_bal = bool(diff == 0)

    return BalanceSheet(
        engagement_id=engagement_id,
        as_at_date=as_at_date,
        division=division,
        equity_and_liabilities_lines=eq_lines,
        assets_lines=asset_lines,
        total_equity_and_liabilities_paise=tot_eq_liab,
        total_assets_paise=tot_assets,
        is_balanced=is_bal,
        difference_paise=diff,
        unmapped_accounts=unmapped,
    )


def build_schedule_iii_profit_and_loss(
    engagement_id: str,
    for_period_ended: str,
    adjusted_tb_lines: list[Any],
) -> ProfitAndLossStatement:
    """Construct Schedule III Statement of Profit & Loss from Adjusted Trial Balance lines."""
    cat_accounts: dict[str, list[Any]] = defaultdict(list)
    for line in adjusted_tb_lines:
        cat = getattr(line, "schedule_iii_category", "") or ""
        if cat:
            cat_accounts[cat].append(line)

    # Revenue
    rev_specs = [
        ("REV-01", "Revenue from Operations", "Sale of Products and Services", "Note 20"),
        ("REV-02", "Other Income", "Interest Income & Miscellaneous", "Note 21"),
    ]
    rev_lines: list[ProfitAndLossLineItem] = []
    tot_rev = 0
    for code, cat, desc, nref in rev_specs:
        accs = cat_accounts.get(cat, [])
        # Income is credit (-net)
        amt = -sum(a.adjusted_net_paise for a in accs) if accs else 0
        tot_rev += amt
        rev_lines.append(
            ProfitAndLossLineItem(
                line_code=code,
                category=cat,
                line_item=desc,
                current_period_paise=amt,
                note_ref=nref,
                mapped_account_codes=[a.account_code for a in accs],
            )
        )

    # Expenses
    exp_specs = [
        ("EXP-01", "Cost of Materials Consumed", "Raw Material Consumption", "Note 22"),
        ("EXP-02", "Employee Benefits Expense", "Salaries, Wages & Staff Welfare", "Note 23"),
        ("EXP-03", "Finance Costs", "Interest Expense & Bank Charges", "Note 24"),
        ("EXP-04", "Depreciation and Amortization", "Depreciation on PPE", "Note 25"),
        ("EXP-05", "Other Expenses", "Manufacturing & Admin Expenses", "Note 26"),
    ]
    exp_lines: list[ProfitAndLossLineItem] = []
    tot_exp = 0
    for code, cat, desc, nref in exp_specs:
        accs = cat_accounts.get(cat, [])
        # Expenses are debit (+net)
        amt = sum(a.adjusted_net_paise for a in accs) if accs else 0
        tot_exp += amt
        exp_lines.append(
            ProfitAndLossLineItem(
                line_code=code,
                category=cat,
                line_item=desc,
                current_period_paise=amt,
                note_ref=nref,
                mapped_account_codes=[a.account_code for a in accs],
            )
        )

    pbt = tot_rev - tot_exp
    # Estimate 25% tax if tax provisions exist, or sum tax provision accounts
    tax_accs = cat_accounts.get("Short-Term Provisions", [])
    tax_amt = max(0, sum(a.adjusted_cr_paise for a in tax_accs if "tax" in a.account_name.lower()))
    pat = pbt - tax_amt

    return ProfitAndLossStatement(
        engagement_id=engagement_id,
        for_period_ended=for_period_ended,
        revenue_lines=rev_lines,
        expense_lines=exp_lines,
        total_revenue_paise=tot_rev,
        total_expenses_paise=tot_exp,
        profit_before_tax_paise=pbt,
        tax_expense_paise=tax_amt,
        profit_after_tax_paise=pat,
    )
