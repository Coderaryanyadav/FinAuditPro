"""Pure domain entities and forensic detection algorithms for Payroll Anomaly and Ghost Employee Scans."""

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class PayrollAnomalyTypeEnum(StrEnum):
    CLEAN_RECORD = "Valid Verified Employee"
    DUPLICATE_BANK_ACCOUNT = "Duplicate Bank Account (Ghost Employee Risk)"
    DUPLICATE_PAN_OR_AADHAAR = "Duplicate PAN / Identity Document"
    PAYMENT_TO_INACTIVE_EMPLOYEE = "Salary Paid Post-Resignation / Inactive Status"
    ROUND_NUMBER_BONUS = "Unusually Large Round-Number Discretionary Payment"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class PayrollAuditRecord(DomainBaseModel):
    """Payroll entry evaluated for identity anomalies and duplicate bank accounts."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    employee_code: str = Field(...)
    employee_name: str = Field(...)
    pan: str = Field(default="")
    bank_account_number: str = Field(...)
    salary_paise: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    resignation_date: str | None = Field(default=None)
    payroll_month: str = Field(...)
    anomaly_type: PayrollAnomalyTypeEnum = Field(default=PayrollAnomalyTypeEnum.CLEAN_RECORD)
    forensic_remark: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class PayrollScanSummary:
    total_payroll_entries: int
    clean_entries_count: int
    ghost_employee_anomalies_count: int
    total_payroll_paise: int
    at_risk_payroll_paise: int
    records: list[PayrollAuditRecord]


class PayrollForensicEngine:
    """Forensic detection engine for ghost employees and payroll anomalies under SA 240 / SA 330."""

    @classmethod
    def scan_payroll_master(
        cls,
        engagement_id: str,
        payroll_entries: list[dict[str, Any]],
    ) -> PayrollScanSummary:
        """Scan payroll registers for duplicate bank accounts, duplicate PANs, and payments to inactive staff."""
        # 1. Build frequency maps
        bank_map = defaultdict(list)
        pan_map = defaultdict(list)

        for p in payroll_entries:
            b_acc = p.get("bank_account_number", "").strip().upper()
            pan = p.get("pan", "").strip().upper()
            e_code = p.get("employee_code", "")
            if b_acc:
                bank_map[b_acc].append(e_code)
            if pan:
                pan_map[pan].append(e_code)

        records = []
        clean_cnt = 0
        anomaly_cnt = 0
        tot_sal_paise = 0
        at_risk_paise = 0

        for p in payroll_entries:
            e_code = p.get("employee_code", "")
            e_name = p.get("employee_name", "Unknown Staff")
            pan = p.get("pan", "").strip().upper()
            b_acc = p.get("bank_account_number", "").strip().upper()
            sal = int(p.get("salary_paise", p.get("salary", 0) * 100))
            is_active = p.get("is_active", True)
            res_d = p.get("resignation_date")
            p_month = p.get("payroll_month", "2026-03")
            tot_sal_paise += sal

            anomaly = PayrollAnomalyTypeEnum.CLEAN_RECORD
            remark = "Verified payroll transaction."

            if not is_active:
                anomaly = PayrollAnomalyTypeEnum.PAYMENT_TO_INACTIVE_EMPLOYEE
                remark = f"Salary of ₹{sal / 100:,.2f} disbursed to inactive/resigned employee (Resigned: {res_d or 'N/A'})."
                anomaly_cnt += 1
                at_risk_paise += sal
            elif b_acc and len(bank_map[b_acc]) > 1:
                anomaly = PayrollAnomalyTypeEnum.DUPLICATE_BANK_ACCOUNT
                shared_with = [c for c in bank_map[b_acc] if c != e_code]
                remark = f"Bank Account '{b_acc}' is shared with employee(s): {', '.join(shared_with)}. High ghost employee risk."
                anomaly_cnt += 1
                at_risk_paise += sal
            elif pan and len(pan_map[pan]) > 1:
                anomaly = PayrollAnomalyTypeEnum.DUPLICATE_PAN_OR_AADHAAR
                shared_with = [c for c in pan_map[pan] if c != e_code]
                remark = f"PAN '{pan}' is duplicated across employee(s): {', '.join(shared_with)}."
                anomaly_cnt += 1
                at_risk_paise += sal
            else:
                clean_cnt += 1

            records.append(
                PayrollAuditRecord(
                    engagement_id=engagement_id,
                    employee_code=e_code,
                    employee_name=e_name,
                    pan=pan,
                    bank_account_number=b_acc,
                    salary_paise=sal,
                    is_active=is_active,
                    resignation_date=res_d,
                    payroll_month=p_month,
                    anomaly_type=anomaly,
                    forensic_remark=remark,
                )
            )

        return PayrollScanSummary(
            total_payroll_entries=len(payroll_entries),
            clean_entries_count=clean_cnt,
            ghost_employee_anomalies_count=anomaly_cnt,
            total_payroll_paise=tot_sal_paise,
            at_risk_payroll_paise=at_risk_paise,
            records=records,
        )
