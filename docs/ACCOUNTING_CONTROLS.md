# FinAuditPro Financial & Accounting Controls (v1.0.0)

## 1. Monetary Precision (Integer Paise Standard)
To eliminate binary floating-point representation artifacts (e.g. `0.1 + 0.2 != 0.3` in standard IEEE 754 float math), FinAuditPro enforces an **exact integer paise** model across all financial entities and calculations:
$$\text{Amount in Paise} = \text{round}(\text{Amount in INR} \times 100)$$

- **Storage**: All database balance columns (`debit_paise`, `credit_paise`, `balance_paise`, `opening_paise`, `adjusted_paise`) are stored as signed 64-bit integers (`INTEGER` in SQLite).
- **Presentation**: Formatted to standard 2-decimal rupee strings (e.g. `₹1,25,000.50`) only at the UI display layer.

---

## 2. Fundamental Accounting Invariants

### Invariant 1: Trial Balance Equality
$$\sum \text{Debit Paise} \equiv \sum \text{Credit Paise}$$
If $\sum \text{Debit} \neq \sum \text{Credit}$, the importer flags the trial balance with an explicit out-of-balance difference amount and prohibits final sign-off.

### Invariant 2: Lead Schedule Roll-Up
The sum of adjusted balances across all trial balance accounts assigned to a Schedule III lead schedule MUST equal the total lead schedule balance:
$$\text{Lead Schedule Total} = \sum_{a \in \text{Accounts}} \text{AdjustedBalance}(a)$$

### Invariant 3: Audit Adjustment Conservation
Every proposed audit journal entry (AJE) must be double-entry balanced:
$$\sum \text{Debit Adjustment Paise} = \sum \text{Credit Adjustment Paise}$$
Unadjusted misstatements are accumulated separately in the SA 450 Misstatement Evaluation schedule.

---

## 3. Deterministic Analytics Engine
1. **Benford's Law Analysis**:
   - First-digit distribution analysis evaluated against Benford's theoretical probability $P(d) = \log_{10}(1 + 1/d)$.
   - $\chi^2$ (Chi-Square) goodness-of-fit statistic calculated deterministically to detect ledger manipulation or synthetic transaction patterns.
2. **Duplicate Payment Detection**:
   - Matching exact `(amount_paise, vendor_id, date)` or same amount within a $\pm 3$-day window.
3. **Outlier Detection**:
   - Statistical z-score computation on transaction distributions across account heads.
4. **Weekend & Holiday Posting**:
   - Automated flagging of high-value journal entries posted on non-working days.
