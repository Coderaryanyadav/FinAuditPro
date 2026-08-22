# Financial Data Ingestion & Deterministic Analytics Engine

FinAuditPro imports client financial statements and executes rigorous, deterministic mathematical analytics with zero LLM guesswork.

---

## 1. Supported Financial Datasets

- **Trial Balance (TB)**: Account codes, descriptions, opening debit/credit, period debit/credit, closing debit/credit.
- **General Ledger (GL)**: Voucher dates, voucher numbers, account names, debit amounts, credit amounts, narrations.
- **Bank Statements**: Transaction dates, descriptions, cheque numbers, withdrawal/deposit amounts, closing balances.

---

## 2. Deterministic Analytics Engine

All currency amounts are stored and calculated in **exact integer paise** to avoid binary floating-point round-off errors.

1. **Benford's 1st Law Analysis**:
   - Analyzes first-digit distribution ($d \in [1..9]$) of transaction amounts.
   - Computes Chi-Square ($\chi^2$) goodness-of-fit against $\log_{10}(1 + 1/d)$ expected frequency.
2. **Duplicate Payment Detector**:
   - Clusters identical amount/vendor payments occurring within a configurable window (e.g. within 30 days).
3. **High-Value Outlier Detection**:
   - Calculates statistical z-score ($\mu \pm 3\sigma$) and flags unusual transaction amounts.
4. **Round-Sum Journal Entry Detector**:
   - Identifies high-value round numbers (e.g. ₹5,00,000.00, ₹10,00,000.00) typical of manual journal entries.
5. **Weekend / Holiday Posting Detector**:
   - Flags journal entries posted on Saturdays or Sundays.

---

## 3. Finding Promotion Workflow

Flagged anomalies appear in the **Financial Data View** exceptions table. Auditors can click **"Promote to Finding"** to create a formal, tracked `Finding` with linked ledger row provenance.
