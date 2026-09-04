"""Pure deterministic data quality validation engine for financial ledgers, journals, and trial balances."""

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Optional
import uuid

from finauditpro.domain.continuous_audit_entities import (
    DataQualityIssue,
    DataQualitySeverityEnum,
    DataQualityTypeEnum,
)


class DataQualityEngine:
    """Deterministic analyzer evaluating structural and integrity properties of financial data."""

    def evaluate_ledger_entries(
        self,
        engagement_id: str,
        dataset_id: str,
        entries: list[dict[str, Any]],
        known_account_codes: Optional[set[str]] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        as_of_date: Optional[date] = None,
    ) -> list[DataQualityIssue]:
        issues: list[DataQualityIssue] = []
        now = datetime.now(timezone.utc)
        eval_date = as_of_date or now.date()

        voucher_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        seen_txn_signatures: dict[str, list[str]] = defaultdict(list)

        for entry in entries:
            row_id = str(entry.get("id") or entry.get("source_row_no") or "UNKNOWN")
            vch_no = str(entry.get("voucher_number") or "").strip()
            acct_code = str(entry.get("account_code") or "").strip()
            acct_name = str(entry.get("account_name") or "").strip()
            narration = str(entry.get("narration") or "").strip()
            created_by = str(entry.get("created_by_raw") or "").strip()
            entry_date_str = str(entry.get("entry_date") or "").strip()
            dr = int(entry.get("debit_paise") or 0)
            cr = int(entry.get("credit_paise") or 0)
            row_engagement_id = entry.get("engagement_id")

            # 1. Invalid Debit/Credit Signs (Negative amounts)
            if dr < 0 or cr < 0:
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.INVALID_DEBIT_CREDIT_SIGN,
                        severity=DataQualitySeverityEnum.HIGH,
                        source="Ledger Integrity Engine",
                        detected_at=now,
                        affected_records=[row_id],
                        description=f"Negative debit/credit amount detected: Dr={dr}, Cr={cr}.",
                    )
                )

            # 2. Missing Account
            if not acct_code and not acct_name:
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.MISSING_ACCOUNT,
                        severity=DataQualitySeverityEnum.CRITICAL,
                        source="Ledger Integrity Engine",
                        detected_at=now,
                        affected_records=[row_id],
                        description="Transaction entry is missing both account code and account name.",
                    )
                )

            # 3. Invalid Account Reference
            if known_account_codes and acct_code and acct_code not in known_account_codes:
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.INVALID_ACCOUNT_REF,
                        severity=DataQualitySeverityEnum.HIGH,
                        source="Ledger Integrity Engine",
                        detected_at=now,
                        affected_records=[row_id],
                        description=f"Account code '{acct_code}' does not exist in the active Chart of Accounts.",
                    )
                )

            # 4. Missing Description
            if not narration:
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.MISSING_DESCRIPTION,
                        severity=DataQualitySeverityEnum.LOW,
                        source="Ledger Integrity Engine",
                        detected_at=now,
                        affected_records=[row_id],
                        description="Transaction has empty or missing narration/description.",
                    )
                )

            # 5. Missing User Reference
            if not created_by:
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.MISSING_USER,
                        severity=DataQualitySeverityEnum.MEDIUM,
                        source="Ledger Integrity Engine",
                        detected_at=now,
                        affected_records=[row_id],
                        description="Transaction record lacks creator/poster attribution.",
                    )
                )

            # 6. Cross-Engagement Reference Leak
            if row_engagement_id and str(row_engagement_id) != str(engagement_id):
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.CROSS_ENGAGEMENT_REF,
                        severity=DataQualitySeverityEnum.CRITICAL,
                        source="Multi-Tenancy Isolation Guard",
                        detected_at=now,
                        affected_records=[row_id],
                        description=f"Entry references engagement '{row_engagement_id}' instead of '{engagement_id}'.",
                    )
                )

            # 7. Date & Period Validations
            parsed_date: Optional[date] = None
            if entry_date_str:
                try:
                    parsed_date = date.fromisoformat(entry_date_str[:10])
                except (ValueError, TypeError):
                    issues.append(
                        DataQualityIssue(
                            issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                            engagement_id=engagement_id,
                            dataset_id=dataset_id,
                            issue_type=DataQualityTypeEnum.INVALID_DATE,
                            severity=DataQualitySeverityEnum.HIGH,
                            source="Ledger Integrity Engine",
                            detected_at=now,
                            affected_records=[row_id],
                            description=f"Invalid unparseable date format '{entry_date_str}'.",
                        )
                    )

            if parsed_date:
                if parsed_date > eval_date:
                    issues.append(
                        DataQualityIssue(
                            issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                            engagement_id=engagement_id,
                            dataset_id=dataset_id,
                            issue_type=DataQualityTypeEnum.FUTURE_DATED,
                            severity=DataQualitySeverityEnum.HIGH,
                            source="Ledger Integrity Engine",
                            detected_at=now,
                            affected_records=[row_id],
                            description=f"Future-dated transaction: {parsed_date} is beyond evaluation date {eval_date}.",
                        )
                    )
                if (period_start and parsed_date < period_start) or (period_end and parsed_date > period_end):
                    issues.append(
                        DataQualityIssue(
                            issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                            engagement_id=engagement_id,
                            dataset_id=dataset_id,
                            issue_type=DataQualityTypeEnum.INVALID_PERIOD,
                            severity=DataQualitySeverityEnum.MEDIUM,
                            source="Ledger Integrity Engine",
                            detected_at=now,
                            affected_records=[row_id],
                            description=f"Transaction date {parsed_date} falls outside audit period ({period_start} to {period_end}).",
                        )
                    )

            # 8. Duplicate transaction signature tracking
            sig = f"{entry_date_str}|{acct_code}|{dr}|{cr}|{narration[:30]}"
            seen_txn_signatures[sig].append(row_id)

            if vch_no:
                voucher_groups[vch_no].append(entry)

        # Evaluate duplicate transactions
        for sig, row_ids in seen_txn_signatures.items():
            if len(row_ids) > 1:
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.DUPLICATE_TXN,
                        severity=DataQualitySeverityEnum.MEDIUM,
                        source="Duplicate Line Detector",
                        detected_at=now,
                        affected_records=row_ids,
                        description=f"Identical transaction signature repeated across {len(row_ids)} ledger lines.",
                    )
                )

        # Evaluate voucher balance and voucher number uniqueness
        for vch_no, vch_entries in voucher_groups.items():
            tot_dr = sum(int(e.get("debit_paise") or 0) for e in vch_entries)
            tot_cr = sum(int(e.get("credit_paise") or 0) for e in vch_entries)
            row_ids = [str(e.get("id") or e.get("source_row_no") or "") for e in vch_entries]

            if tot_dr != tot_cr:
                diff = abs(tot_dr - tot_cr)
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.UNBALANCED_JOURNAL,
                        severity=DataQualitySeverityEnum.CRITICAL,
                        source="Journal Balancing Engine",
                        detected_at=now,
                        affected_records=row_ids,
                        description=f"Voucher {vch_no} is unbalanced: Dr={tot_dr} paise, Cr={tot_cr} paise (Diff={diff}).",
                    )
                )

            # Check if same voucher number is used across disparate dates
            dates = {str(e.get("entry_date") or "")[:10] for e in vch_entries if e.get("entry_date")}
            if len(dates) > 1:
                issues.append(
                    DataQualityIssue(
                        issue_id=f"DQI-{uuid.uuid4().hex[:8].upper()}",
                        engagement_id=engagement_id,
                        dataset_id=dataset_id,
                        issue_type=DataQualityTypeEnum.DUPLICATE_JOURNAL_ID,
                        severity=DataQualitySeverityEnum.HIGH,
                        source="Journal Integrity Engine",
                        detected_at=now,
                        affected_records=row_ids,
                        description=f"Voucher number {vch_no} reused across divergent dates: {sorted(list(dates))}.",
                    )
                )

        return issues
