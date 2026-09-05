"""Deterministic journal entry risk scoring and Benford's Law analytical anomaly detection."""

import math
import uuid
from datetime import date, datetime
from typing import Any

from finauditpro.domain.continuous_audit_entities import (
    AlertSeverityEnum,
    AlertTypeEnum,
    BenfordAnalysisResult,
    ContinuousAlert,
    RiskFactorContribution,
)


class JournalAnalyticsEngine:
    """Evaluates individual journals and transaction populations for deterministic risk signals."""

    BENFORD_EXPECTED_FIRST_DIGIT = {
        1: 0.30103,
        2: 0.17609,
        3: 0.12494,
        4: 0.09691,
        5: 0.07918,
        6: 0.06695,
        7: 0.05799,
        8: 0.05115,
        9: 0.04576,
    }

    def __init__(self, period_end_date: date | None = None, high_value_threshold_paise: int = 50_00_00_00):
        # Default high value threshold: 50 Lakhs INR (5,000,000 INR = 50,00,00,00 paise)
        self.period_end_date = period_end_date
        self.high_value_threshold_paise = high_value_threshold_paise

    def evaluate_journal_entry(
        self,
        engagement_id: str,
        journal_data: dict[str, Any],
    ) -> ContinuousAlert | None:
        """Calculates deterministic risk factors and produces an alert if risk exceeds baseline threshold."""
        factors: list[RiskFactorContribution] = []
        score = 0.0

        vch_no = str(journal_data.get("voucher_number") or journal_data.get("id") or "UNKNOWN")
        vch_type = str(journal_data.get("voucher_type") or "").upper()
        narration = str(journal_data.get("narration") or "").upper()
        entry_date_str = str(journal_data.get("entry_date") or "")
        created_by = str(journal_data.get("created_by_raw") or "").lower()
        amount_paise = int(journal_data.get("debit_paise") or journal_data.get("credit_paise") or 0)
        acct_code = str(journal_data.get("account_code") or "")
        acct_name = str(journal_data.get("account_name") or "").upper()

        parsed_date: date | None = None
        if entry_date_str:
            try:
                parsed_date = date.fromisoformat(entry_date_str[:10])
            except (ValueError, TypeError):
                pass

        # 1. Round-number pattern evaluation
        if amount_paise > 0:
            rupees = amount_paise // 100
            if rupees >= 10_000 and (rupees % 100_000 == 0 or rupees % 50_000 == 0):
                factors.append(
                    RiskFactorContribution(
                        factor_name="Round-Number Amount Pattern",
                        score_contribution=20.0,
                        description=f"Transaction amount ₹{rupees:,.2f} is an exact round-number multiple.",
                    )
                )
                score += 20.0
            elif str(rupees).endswith("99999") or str(rupees).endswith("9999"):
                factors.append(
                    RiskFactorContribution(
                        factor_name="Threshold-Proximity Pattern",
                        score_contribution=20.0,
                        description=f"Transaction amount ₹{rupees:,.2f} ends in repeating 9s near standard approval thresholds.",
                    )
                )
                score += 20.0

        # 2. High-value transaction evaluation
        if amount_paise >= self.high_value_threshold_paise:
            factors.append(
                RiskFactorContribution(
                    factor_name="High-Value Transaction",
                    score_contribution=25.0,
                    description=f"Transaction value ₹{amount_paise / 100:,.2f} exceeds high-value monitoring threshold.",
                )
            )
            score += 25.0

        # 3. Timing: Weekend or Period-End
        if parsed_date:
            # Weekend (Saturday=5, Sunday=6)
            if parsed_date.weekday() in (5, 6):
                factors.append(
                    RiskFactorContribution(
                        factor_name="Weekend Posting",
                        score_contribution=15.0,
                        description=f"Posted on {parsed_date.strftime('%A')} ({parsed_date.isoformat()}) outside standard working days.",
                    )
                )
                score += 15.0

            # Period-End Posting (within 7 days of financial year end or month end)
            if self.period_end_date:
                days_to_end = (self.period_end_date - parsed_date).days
                if 0 <= days_to_end <= 7:
                    factors.append(
                        RiskFactorContribution(
                            factor_name="Period-End Close Posting",
                            score_contribution=25.0,
                            description=f"Posted {days_to_end} days prior to financial period close ({self.period_end_date}).",
                        )
                    )
                    score += 25.0
                elif days_to_end < 0:
                    factors.append(
                        RiskFactorContribution(
                            factor_name="Post-Closing Journal Entry",
                            score_contribution=30.0,
                            description=f"Dated {abs(days_to_end)} days after period close date {self.period_end_date}.",
                        )
                    )
                    score += 30.0

        # 4. Entry Type: Manual Journal or Reversing Journal
        if "MANUAL" in vch_type or "JOURNAL" in vch_type or "JV" in vch_type:
            factors.append(
                RiskFactorContribution(
                    factor_name="Manual Journal Entry",
                    score_contribution=20.0,
                    description=f"Recorded as manual journal voucher type '{vch_type}'.",
                )
            )
            score += 20.0

        if "REVERS" in narration or "CANCEL" in narration or "RECTIF" in narration:
            factors.append(
                RiskFactorContribution(
                    factor_name="Reversing/Rectification Entry",
                    score_contribution=15.0,
                    description=f"Narration indicates journal reversal or adjustment: '{narration[:60]}'.",
                )
            )
            score += 15.0

        # 5. Rare/Unusual Account Pairing Signals
        if "CASH" in acct_name and ("REVENUE" in narration or "SALES" in narration or "INCOME" in narration):
            factors.append(
                RiskFactorContribution(
                    factor_name="Unusual Account Combination",
                    score_contribution=20.0,
                    description="Direct manual cash entry associated with operating revenue.",
                )
            )
            score += 20.0

        # 6. User Behavior: System Admin or Shared Account
        if any(unusual in created_by for unusual in ["admin", "root", "system", "temp", "guest"]):
            factors.append(
                RiskFactorContribution(
                    factor_name="Privileged/Generic User Poster",
                    score_contribution=15.0,
                    description=f"Journal posted by administrative or generic account '{created_by}'.",
                )
            )
            score += 15.0

        # Only emit alert if score reaches at least 30.0
        if score < 30.0:
            return None

        severity = AlertSeverityEnum.LOW
        if score >= 70.0:
            severity = AlertSeverityEnum.CRITICAL
        elif score >= 50.0:
            severity = AlertSeverityEnum.HIGH
        elif score >= 30.0:
            severity = AlertSeverityEnum.MEDIUM

        dedup_sig = f"{vch_no}|{amount_paise}|{entry_date_str}|{acct_code}"
        dedup_hash = f"JE-RISK-{uuid.uuid5(uuid.NAMESPACE_DNS, dedup_sig).hex[:12]}"

        return ContinuousAlert(
            alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
            engagement_id=engagement_id,
            alert_type=AlertTypeEnum.JOURNAL_RISK,
            severity=severity,
            title=f"Potential Risk Signal: Unusual Journal Entry {vch_no}",
            description=f"Evaluated journal voucher {vch_no} exhibits risk score {score:.0f}/100 based on {len(factors)} deterministic risk factors.",
            source="Deterministic Journal Risk Engine",
            detected_at=datetime.now(),
            affected_data={
                "voucher_number": vch_no,
                "voucher_type": vch_type,
                "entry_date": entry_date_str,
                "account_code": acct_code,
                "account_name": acct_name,
                "amount_paise": amount_paise,
                "created_by": created_by,
                "narration": narration,
            },
            risk_score=score,
            risk_factors=factors,
            dedup_hash=dedup_hash,
            model_rule_version="v1.0-deterministic",
        )

    def analyze_benford_distribution(
        self,
        amounts_paise: list[int],
    ) -> BenfordAnalysisResult:
        """Applies Benford's First-Digit Law as a supporting analytical anomaly indicator."""
        eligible_digits: list[int] = []
        excluded_count = 0

        for amt in amounts_paise:
            # Exclude zero, negative, or trivial values (< 10.00 INR = 1000 paise)
            if amt < 1000:
                excluded_count += 1
                continue
            first_digit = int(str(amt)[0])
            if 1 <= first_digit <= 9:
                eligible_digits.append(first_digit)
            else:
                excluded_count += 1

        total_eligible = len(eligible_digits)
        if total_eligible == 0:
            return BenfordAnalysisResult(
                population_count=len(amounts_paise),
                eligible_count=0,
                excluded_count=excluded_count,
                digit_type="FIRST_DIGIT",
                observed_distribution={d: 0.0 for d in range(1, 10)},
                expected_distribution=self.BENFORD_EXPECTED_FIRST_DIGIT.copy(),
                chi_square_stat=0.0,
                p_value_approx=1.0,
                deviation_detected=False,
                interpretation="Insufficient eligible population to perform Benford first-digit frequency analysis.",
            )

        counts = {d: 0 for d in range(1, 10)}
        for d in eligible_digits:
            counts[d] += 1

        observed_dist = {d: counts[d] / total_eligible for d in range(1, 10)}

        # Chi-Square calculation: sum((O - E)^2 / E)
        chi_square = 0.0
        for d in range(1, 10):
            observed_cnt = counts[d]
            expected_cnt = self.BENFORD_EXPECTED_FIRST_DIGIT[d] * total_eligible
            if expected_cnt > 0:
                chi_square += ((observed_cnt - expected_cnt) ** 2) / expected_cnt

        # 8 degrees of freedom critical value at alpha=0.05 is 15.507, alpha=0.01 is 20.090
        deviation = chi_square > 15.507
        p_val_approx = math.exp(-chi_square / 16.0) if chi_square > 0 else 1.0

        interpretation = (
            f"Population shows statistically significant divergence from expected Benford distribution "
            f"(Chi-Sq: {chi_square:.2f}, df=8). Requires auditor inquiry into transaction generation processes."
            if deviation
            else f"First-digit distribution conforms to expected natural logarithmic distribution (Chi-Sq: {chi_square:.2f})."
        )

        return BenfordAnalysisResult(
            population_count=len(amounts_paise),
            eligible_count=total_eligible,
            excluded_count=excluded_count,
            digit_type="FIRST_DIGIT",
            observed_distribution=observed_dist,
            expected_distribution=self.BENFORD_EXPECTED_FIRST_DIGIT.copy(),
            chi_square_stat=round(chi_square, 3),
            p_value_approx=round(min(1.0, max(0.0, p_val_approx)), 4),
            deviation_detected=deviation,
            interpretation=interpretation,
        )
