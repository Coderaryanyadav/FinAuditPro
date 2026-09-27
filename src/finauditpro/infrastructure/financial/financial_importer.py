"""Financial data importer for Excel/CSV files with Decimal currency parsing, day-first date parsing, and CSV formula injection protection."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finauditpro.application.financial_dtos import ValidationPreviewDTO, ValidationRowPreviewDTO
from finauditpro.domain.financial_entities import (
    BankTransaction,
    DatasetTypeEnum,
    LedgerEntry,
    RowError,
    TrialBalanceLine,
    TrialBalanceSummary,
)
from finauditpro.domain.value_objects import Money
from finauditpro.infrastructure.financial.currency_parser import (
    parse_indian_currency,
    parse_indian_date,
    sanitize_export_cell,
)

__all__ = [
    "FinancialImportError",
    "FinancialImporter",
    "ImportResult",
    "parse_indian_currency",
    "parse_indian_date",
    "sanitize_export_cell",
]


class FinancialImportError(Exception):
    """Raised when dataset file reading or column mapping validation fails."""

    pass


@dataclass
class ImportResult:
    total_rows: int
    valid_rows: list[Any]
    errors: list[RowError]
    summary: TrialBalanceSummary | None = None


class FinancialImporter:
    """Importer converting raw tabular data into validated domain models."""

    @staticmethod
    def read_tabular_rows(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
        ext = file_path.suffix.lower()
        rows, headers = [], []
        if ext in (".xlsx", ".xls"):
            import openpyxl

            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            iter_rows = sheet.iter_rows(values_only=True)
            header_row = next(iter_rows, None)
            if not header_row:
                raise FinancialImportError("Empty Excel sheet.")
            headers = [str(h or "").strip() for h in header_row]
            for r in iter_rows:
                if any(r):
                    rows.append({
                        headers[i]: str(r[i]).strip() if i < len(r) and r[i] is not None else ""
                        for i in range(len(headers))
                    })
            wb.close()
        elif ext == ".csv":
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header_row = next(reader, None)
                if not header_row:
                    raise FinancialImportError("Empty CSV file.")
                headers = [str(h or "").strip() for h in header_row]
                for r in reader:
                    if any(r):
                        rows.append({
                            headers[i]: r[i].strip() if i < len(r) else ""
                            for i in range(len(headers))
                        })
        else:
            raise FinancialImportError(f"Unsupported dataset extension: '{ext}'")
        return headers, rows

    @classmethod
    def validate_and_preview(
        cls,
        dataset_type: DatasetTypeEnum,
        rows: list[dict[str, str]],
        mappings: dict[str, str],
        file_path: str = "",
    ) -> ValidationPreviewDTO:
        if dataset_type == DatasetTypeEnum.TRIAL_BALANCE:
            imp_res = cls.import_trial_balance("preview", rows, mappings)
            tot_dr = imp_res.summary.total_debit_paise if imp_res.summary else 0
            tot_cr = imp_res.summary.total_credit_paise if imp_res.summary else 0
            is_bal = imp_res.summary.is_balanced if imp_res.summary else True
            disc = imp_res.summary.period_discrepancy_paise if imp_res.summary else 0
        elif dataset_type == DatasetTypeEnum.BANK_STATEMENT:
            imp_res = cls.import_bank_statement("preview", rows, mappings)
            tot_dr = sum(t.debit_paise for t in imp_res.valid_rows)
            tot_cr = sum(t.credit_paise for t in imp_res.valid_rows)
            is_bal, disc = True, 0
        else:
            imp_res = cls.import_general_ledger("preview", rows, mappings)
            tot_dr = sum(e.debit_paise for e in imp_res.valid_rows)
            tot_cr = sum(e.credit_paise for e in imp_res.valid_rows)
            is_bal, disc = True, 0

        seen_keys: set[str] = set()
        dup_count, dup_errors = 0, []
        for idx, r in enumerate(rows, start=2):
            v_no, tx_id = (
                r.get(mappings.get("voucher_number", ""), "").strip(),
                r.get(mappings.get("transaction_id", ""), "").strip(),
            )
            key = v_no or tx_id
            if key:
                if key in seen_keys:
                    dup_count += 1
                    dup_errors.append(
                        RowError(
                            row_no=idx,
                            column_name="voucher/transaction_id",
                            raw_value=key,
                            error_reason=f"Duplicate identifier: '{key}'",
                        )
                    )
                else:
                    seen_keys.add(key)

        all_errors = imp_res.errors + dup_errors
        sample_preview = [
            ValidationRowPreviewDTO(
                row_no=idx,
                is_valid=not any(e.row_no == idx for e in all_errors),
                data=r,
                errors=[e.error_reason for e in all_errors if e.row_no == idx],
            )
            for idx, r in enumerate(rows[:10], start=2)
        ]
        val_passed = (len(all_errors) == 0) and is_bal
        msg = (
            f"Validation passed: {len(imp_res.valid_rows)}/{len(rows)} valid records."
            if val_passed
            else f"Validation issues: {len(all_errors)} errors. Balanced: {is_bal}."
        )

        return ValidationPreviewDTO(
            file_path=file_path,
            dataset_type=dataset_type,
            total_rows=len(rows),
            valid_rows_count=len(imp_res.valid_rows),
            error_count=len(all_errors),
            duplicate_count=dup_count,
            total_debit_paise=tot_dr,
            total_credit_paise=tot_cr,
            is_balanced=is_bal,
            discrepancy_paise=disc,
            validation_passed=val_passed,
            summary_message=msg,
            errors=all_errors,
            sample_preview=sample_preview,
        )

    @classmethod
    def import_trial_balance(
        cls, dataset_id: str, rows: list[dict[str, str]], mappings: dict[str, str]
    ) -> ImportResult:
        valid_lines, errors = [], []
        col_code, col_name, col_type = (
            mappings.get("account_code"),
            mappings.get("account_name", "Account Name"),
            mappings.get("account_type"),
        )
        col_op_dr, col_op_cr = mappings.get("opening_dr"), mappings.get("opening_cr")
        col_dr, col_cr = mappings.get("debit"), mappings.get("credit")
        col_cl_dr, col_cl_cr = mappings.get("closing_dr"), mappings.get("closing_cr")

        for idx, r in enumerate(rows, start=2):
            acc_name = r.get(col_name, "").strip() if col_name else ""
            if not acc_name and col_code:
                acc_name = r.get(col_code, "").strip()
            if not acc_name:
                errors.append(
                    RowError(
                        row_no=idx,
                        column_name="account_name",
                        raw_value="",
                        error_reason="Missing Account Name",
                    )
                )
                continue
            try:
                op_dr = parse_indian_currency(r.get(col_op_dr)).paise if col_op_dr else 0
                op_cr = parse_indian_currency(r.get(col_op_cr)).paise if col_op_cr else 0
                dr = parse_indian_currency(r.get(col_dr)).paise if col_dr else 0
                cr = parse_indian_currency(r.get(col_cr)).paise if col_cr else 0
                cl_dr = parse_indian_currency(r.get(col_cl_dr)).paise if col_cl_dr else 0
                cl_cr = parse_indian_currency(r.get(col_cl_cr)).paise if col_cl_cr else 0
                valid_lines.append(
                    TrialBalanceLine(
                        dataset_id=dataset_id,
                        source_row_no=idx,
                        account_code=r.get(col_code, "").strip() if col_code else None,
                        account_name=acc_name,
                        account_type=r.get(col_type, "").strip() if col_type else None,
                        opening_dr_paise=op_dr,
                        opening_cr_paise=op_cr,
                        debit_paise=dr,
                        credit_paise=cr,
                        closing_dr_paise=cl_dr,
                        closing_cr_paise=cl_cr,
                        raw_values=r,
                    )
                )
            except ValueError as val_ex:
                errors.append(
                    RowError(
                        row_no=idx, column_name="amount", raw_value=str(r), error_reason=str(val_ex)
                    )
                )

        t_op_dr, t_op_cr = sum(l.opening_dr_paise for l in valid_lines), sum(
            l.opening_cr_paise for l in valid_lines
        )
        t_dr, t_cr = sum(l.debit_paise for l in valid_lines), sum(
            l.credit_paise for l in valid_lines
        )
        t_cl_dr, t_cl_cr = sum(l.closing_dr_paise for l in valid_lines), sum(
            l.closing_cr_paise for l in valid_lines
        )
        summary = TrialBalanceSummary(
            total_opening_dr_paise=t_op_dr,
            total_opening_cr_paise=t_op_cr,
            total_debit_paise=t_dr,
            total_credit_paise=t_cr,
            total_closing_dr_paise=t_cl_dr,
            total_closing_cr_paise=t_cl_cr,
        )

        if not summary.is_period_balanced and (t_dr > 0 or t_cr > 0):
            d_p = summary.period_discrepancy_paise
            errors.append(
                RowError(
                    row_no=1,
                    column_name="debit/credit",
                    raw_value=f"Debits: {Money(paise=t_dr).format_indian()}, Credits: {Money(paise=t_cr).format_indian()}",
                    error_reason=f"Trial Balance movement out of balance by {Money(paise=abs(d_p)).format_indian()} ({d_p} paise).",
                )
            )
        if not summary.is_closing_balanced and (t_cl_dr > 0 or t_cl_cr > 0):
            d_c = summary.closing_discrepancy_paise
            errors.append(
                RowError(
                    row_no=1,
                    column_name="closing_dr/closing_cr",
                    raw_value=f"Closing Dr: {Money(paise=t_cl_dr).format_indian()}, Closing Cr: {Money(paise=t_cl_cr).format_indian()}",
                    error_reason=f"Trial Balance closing balances out of balance by {Money(paise=abs(d_c)).format_indian()} ({d_c} paise).",
                )
            )
        return ImportResult(
            total_rows=len(rows), valid_rows=valid_lines, errors=errors, summary=summary
        )

    @classmethod
    def import_general_ledger(
        cls, dataset_id: str, rows: list[dict[str, str]], mappings: dict[str, str]
    ) -> ImportResult:
        valid_entries, errors = [], []
        col_date, col_type, col_no = (
            mappings.get("date"),
            mappings.get("voucher_type"),
            mappings.get("voucher_number"),
        )
        col_code, col_name = mappings.get("account_code"), mappings.get("account_name")
        col_dr, col_cr = mappings.get("debit"), mappings.get("credit")
        col_narr, col_ref, col_by = (
            mappings.get("narration"),
            mappings.get("reference"),
            mappings.get("created_by"),
        )

        for idx, r in enumerate(rows, start=2):
            dt_str = None
            if col_date and r.get(col_date):
                try:
                    dt_str = parse_indian_date(r.get(col_date))
                except ValueError as dt_ex:
                    errors.append(
                        RowError(
                            row_no=idx,
                            column_name="date",
                            raw_value=str(r.get(col_date)),
                            error_reason=str(dt_ex),
                        )
                    )
                    continue
            try:
                dr = parse_indian_currency(r.get(col_dr)).paise if col_dr else 0
                cr = parse_indian_currency(r.get(col_cr)).paise if col_cr else 0
                valid_entries.append(
                    LedgerEntry(
                        dataset_id=dataset_id,
                        source_row_no=idx,
                        entry_date=dt_str,
                        voucher_type=r.get(col_type, "").strip() if col_type else None,
                        voucher_number=r.get(col_no, "").strip() if col_no else None,
                        account_code=r.get(col_code, "").strip() if col_code else None,
                        account_name=r.get(col_name, "").strip() if col_name else "",
                        debit_paise=dr,
                        credit_paise=cr,
                        narration=r.get(col_narr, "").strip() if col_narr else None,
                        reference=r.get(col_ref, "").strip() if col_ref else None,
                        created_by_raw=r.get(col_by, "").strip() if col_by else None,
                        raw_values=r,
                    )
                )
            except ValueError as val_ex:
                errors.append(
                    RowError(
                        row_no=idx, column_name="amount", raw_value=str(r), error_reason=str(val_ex)
                    )
                )
        return ImportResult(total_rows=len(rows), valid_rows=valid_entries, errors=errors)

    @classmethod
    def import_bank_statement(
        cls, dataset_id: str, rows: list[dict[str, str]], mappings: dict[str, str]
    ) -> ImportResult:
        valid_txns, errors = [], []
        col_date, col_val_date = mappings.get("date"), mappings.get("value_date")
        col_txn_id, col_desc = mappings.get("transaction_id"), mappings.get(
            "description", mappings.get("narration")
        )
        col_dr, col_cr, col_bal, col_ref = (
            mappings.get("debit"),
            mappings.get("credit"),
            mappings.get("balance"),
            mappings.get("reference"),
        )

        for idx, r in enumerate(rows, start=2):
            dt_str = None
            if col_date and r.get(col_date):
                try:
                    dt_str = parse_indian_date(r.get(col_date))
                except ValueError as dt_ex:
                    errors.append(
                        RowError(
                            row_no=idx,
                            column_name="date",
                            raw_value=str(r.get(col_date)),
                            error_reason=str(dt_ex),
                        )
                    )
                    continue
            val_dt_str = None
            if col_val_date and r.get(col_val_date):
                try:
                    val_dt_str = parse_indian_date(r.get(col_val_date))
                except Exception:
                    val_dt_str = None
            try:
                dr = parse_indian_currency(r.get(col_dr)).paise if col_dr else 0
                cr = parse_indian_currency(r.get(col_cr)).paise if col_cr else 0
                bal = parse_indian_currency(r.get(col_bal)).paise if col_bal else 0
                desc = r.get(col_desc, "").strip() if col_desc else f"Bank Transaction #{idx}"
                valid_txns.append(
                    BankTransaction(
                        dataset_id=dataset_id,
                        source_row_no=idx,
                        txn_date=dt_str,
                        value_date=val_dt_str,
                        txn_id=r.get(col_txn_id, "").strip() if col_txn_id else None,
                        description=desc,
                        debit_paise=dr,
                        credit_paise=cr,
                        balance_paise=bal,
                        reference=r.get(col_ref, "").strip() if col_ref else None,
                        raw_values=r,
                    )
                )
            except ValueError as val_ex:
                errors.append(
                    RowError(
                        row_no=idx, column_name="amount", raw_value=str(r), error_reason=str(val_ex)
                    )
                )
        return ImportResult(total_rows=len(rows), valid_rows=valid_txns, errors=errors)
