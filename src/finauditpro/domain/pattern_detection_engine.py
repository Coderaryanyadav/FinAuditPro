"""Pattern detection engine for duplicates, transaction splitting, related party, tax, and control exceptions."""

from collections import defaultdict
from datetime import date, datetime
import math
from typing import Any, Optional
import uuid

from finauditpro.domain.continuous_audit_entities import (
    AlertSeverityEnum,
    AlertTypeEnum,
    ContinuousAlert,
    RiskFactorContribution,
)


class PatternDetectionEngine:
    """Deterministic pattern recognition engine detecting duplicates, split transactions, and control breaks."""

    def __init__(self, approval_threshold_paise: int = 10_00_00_00):
        # Default authorization threshold: 1 Lakh INR (10,000,000 paise)
        self.approval_threshold_paise = approval_threshold_paise

    def detect_duplicate_transactions(
        self,
        engagement_id: str,
        transactions: list[dict[str, Any]],
        date_window_days: int = 5,
    ) -> list[ContinuousAlert]:
        """Identifies exact and high-similarity duplicate entries across vendor, amount, invoice, or dates."""
        alerts: list[ContinuousAlert] = []
        now = datetime.now()

        # Group by (vendor/party, amount_paise)
        groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        for txn in transactions:
            party = str(txn.get("account_name") or txn.get("party_name") or "").strip().upper()
            amt = int(txn.get("debit_paise") or txn.get("credit_paise") or txn.get("amount_paise") or 0)
            if amt > 0 and party:
                groups[(party, amt)].append(txn)

        for (party, amt), items in groups.items():
            if len(items) < 2:
                continue

            # Check date proximity and reference similarity
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    t1, t2 = items[i], items[j]
                    d1_str = str(t1.get("entry_date") or t1.get("txn_date") or "")[:10]
                    d2_str = str(t2.get("entry_date") or t2.get("txn_date") or "")[:10]
                    ref1 = str(t1.get("reference") or t1.get("voucher_number") or "").strip().upper()
                    ref2 = str(t2.get("reference") or t2.get("voucher_number") or "").strip().upper()

                    close_dates = False
                    if d1_str and d2_str:
                        try:
                            delta = abs((date.fromisoformat(d1_str) - date.fromisoformat(d2_str)).days)
                            close_dates = delta <= date_window_days
                        except (ValueError, TypeError):
                            pass

                    # Duplicate candidate found if identical reference or identical amount + party + close dates
                    if (ref1 and ref1 == ref2) or close_dates:
                        id1 = str(t1.get("id") or t1.get("voucher_number") or i)
                        id2 = str(t2.get("id") or t2.get("voucher_number") or j)
                        dedup_hash = f"DUP-{sorted([id1, id2])[0]}-{sorted([id1, id2])[1]}"

                        factors = [
                            RiskFactorContribution(
                                factor_name="Matching Vendor & Amount",
                                score_contribution=35.0,
                                description=f"Vendor '{party}' with identical amount ₹{amt / 100:,.2f}.",
                            )
                        ]
                        score = 35.0

                        if ref1 and ref1 == ref2:
                            factors.append(
                                RiskFactorContribution(
                                    factor_name="Identical Invoice/Reference Code",
                                    score_contribution=40.0,
                                    description=f"Both entries share identical reference '{ref1}'.",
                                )
                            )
                            score += 40.0
                        if close_dates:
                            factors.append(
                                RiskFactorContribution(
                                    factor_name="Proximity in Posting Dates",
                                    score_contribution=25.0,
                                    description=f"Entries occurred within {date_window_days} days ({d1_str} vs {d2_str}).",
                                )
                            )
                            score += 25.0

                        severity = AlertSeverityEnum.HIGH if score >= 70 else AlertSeverityEnum.MEDIUM
                        alerts.append(
                            ContinuousAlert(
                                alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                                engagement_id=engagement_id,
                                alert_type=AlertTypeEnum.DUPLICATE_TRANSACTION,
                                severity=severity,
                                title=f"Potential Risk Signal: Suspected Duplicate Transaction ({party})",
                                description=(
                                    f"Detected potential duplicate entry for {party} with identical amount "
                                    f"₹{amt / 100:,.2f} across vouchers/records {id1} and {id2}."
                                ),
                                source="Deterministic Duplicate Detector",
                                detected_at=now,
                                affected_data={
                                    "party_name": party,
                                    "amount_paise": amt,
                                    "record_ids": [id1, id2],
                                    "reference_1": ref1,
                                    "reference_2": ref2,
                                    "date_1": d1_str,
                                    "date_2": d2_str,
                                },
                                risk_score=score,
                                risk_factors=factors,
                                dedup_hash=dedup_hash,
                            )
                        )

        return alerts

    def detect_split_transactions(
        self,
        engagement_id: str,
        transactions: list[dict[str, Any]],
        window_days: int = 7,
    ) -> list[ContinuousAlert]:
        """Detects clustered sub-threshold transactions that aggregate above authorization limit."""
        alerts: list[ContinuousAlert] = []
        now = datetime.now()
        thresh = self.approval_threshold_paise
        lower_bound = int(thresh * 0.70)  # Between 70% and 99.9% of threshold

        # Group by party and user
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for txn in transactions:
            amt = int(txn.get("debit_paise") or txn.get("credit_paise") or txn.get("amount_paise") or 0)
            party = str(txn.get("account_name") or txn.get("party_name") or "").strip().upper()
            if lower_bound <= amt < thresh and party:
                grouped[party].append(txn)

        for party, items in grouped.items():
            if len(items) < 2:
                continue

            # Sort by date
            sorted_items = sorted(
                items,
                key=lambda x: str(x.get("entry_date") or x.get("txn_date") or "9999-99-99"),
            )

            # Check sliding window
            for i in range(len(sorted_items) - 1):
                cluster = [sorted_items[i]]
                d_start_str = str(sorted_items[i].get("entry_date") or "")[:10]
                try:
                    d_start = date.fromisoformat(d_start_str)
                except (ValueError, TypeError):
                    continue

                for j in range(i + 1, len(sorted_items)):
                    d_next_str = str(sorted_items[j].get("entry_date") or "")[:10]
                    try:
                        d_next = date.fromisoformat(d_next_str)
                        if (d_next - d_start).days <= window_days:
                            cluster.append(sorted_items[j])
                    except (ValueError, TypeError):
                        pass

                if len(cluster) >= 2:
                    total_agg = sum(
                        int(x.get("debit_paise") or x.get("credit_paise") or x.get("amount_paise") or 0)
                        for x in cluster
                    )
                    if total_agg >= thresh:
                        vchs = [str(x.get("voucher_number") or x.get("id") or "") for x in cluster]
                        factors = [
                            RiskFactorContribution(
                                factor_name="Sub-Threshold Clustered Amounts",
                                score_contribution=35.0,
                                description=(
                                    f"{len(cluster)} transactions individually below ₹{thresh / 100:,.2f} "
                                    f"aggregate to ₹{total_agg / 100:,.2f}."
                                ),
                            ),
                            RiskFactorContribution(
                                factor_name="Common Vendor & Temporal Window",
                                score_contribution=30.0,
                                description=f"All {len(cluster)} transactions posted for vendor '{party}' within {window_days} days.",
                            ),
                        ]
                        score = 65.0
                        alerts.append(
                            ContinuousAlert(
                                alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                                engagement_id=engagement_id,
                                alert_type=AlertTypeEnum.SPLIT_TRANSACTION,
                                severity=AlertSeverityEnum.HIGH,
                                title=f"Potential Risk Signal: Sub-Threshold Transaction Splitting ({party})",
                                description=(
                                    f"Series of {len(cluster)} transactions for vendor '{party}' individually below approval "
                                    f"threshold ₹{thresh / 100:,.2f} aggregate to ₹{total_agg / 100:,.2f} within {window_days} days. Requires review."
                                ),
                                source="Split Transaction Pattern Engine",
                                detected_at=now,
                                affected_data={
                                    "party_name": party,
                                    "voucher_numbers": vchs,
                                    "aggregate_amount_paise": total_agg,
                                    "threshold_paise": thresh,
                                    "cluster_size": len(cluster),
                                },
                                risk_score=score,
                                risk_factors=factors,
                                dedup_hash=f"SPLIT-{party}-{'-'.join(sorted(vchs)[:3])}",
                            )
                        )
                        break  # Break out of inner cluster to avoid redundant alerts on same group

        return alerts

    def evaluate_control_monitoring(
        self,
        engagement_id: str,
        action_type: str,
        maker_id: str,
        reviewer_id: Optional[str],
        amount_paise: int = 0,
        is_engagement_locked: bool = False,
    ) -> list[ContinuousAlert]:
        """Detects separation-of-duties violations, self-reviews, and unauthorized modifications."""
        alerts: list[ContinuousAlert] = []
        now = datetime.now()

        # 1. Maker == Reviewer Violation
        if reviewer_id and maker_id.strip().lower() == reviewer_id.strip().lower():
            factors = [
                RiskFactorContribution(
                    factor_name="Separation of Duties Break",
                    score_contribution=50.0,
                    description=f"Same user '{maker_id}' acted as both creator and reviewer/approver.",
                )
            ]
            alerts.append(
                ContinuousAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                    engagement_id=engagement_id,
                    alert_type=AlertTypeEnum.CONTROL_VIOLATION,
                    severity=AlertSeverityEnum.CRITICAL,
                    title="Control Exception: Maker and Reviewer Are Identical",
                    description=f"Self-approval detected on '{action_type}'. Preparer '{maker_id}' also signed off as reviewer.",
                    source="Continuous Control Monitor",
                    detected_at=now,
                    affected_data={"action_type": action_type, "user_id": maker_id},
                    risk_score=85.0,
                    risk_factors=factors,
                    dedup_hash=f"SOD-{maker_id}-{action_type}",
                )
            )

        # 2. Locked Engagement Modification Attempt
        if is_engagement_locked:
            factors = [
                RiskFactorContribution(
                    factor_name="Locked File Mutation Attempt",
                    score_contribution=60.0,
                    description="Action attempted on a finalized and cryptographically locked audit engagement.",
                )
            ]
            alerts.append(
                ContinuousAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                    engagement_id=engagement_id,
                    alert_type=AlertTypeEnum.CONTROL_VIOLATION,
                    severity=AlertSeverityEnum.CRITICAL,
                    title="Control Exception: Modification Attempted on Locked Engagement",
                    description=f"Unauthorized modification action '{action_type}' blocked against finalized engagement {engagement_id}.",
                    source="Continuous Control Monitor",
                    detected_at=now,
                    affected_data={"action_type": action_type, "user_id": maker_id},
                    risk_score=95.0,
                    risk_factors=factors,
                    dedup_hash=f"LOCK-BREACH-{engagement_id}-{action_type}",
                )
            )

        return alerts
