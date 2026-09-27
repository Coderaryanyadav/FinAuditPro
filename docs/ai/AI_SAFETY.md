# FinAuditPro — AI Safety & Guardrails

## 1. Guardrail Tenets
1. **Deterministic Calculation Guardrail:** The LLM is strictly prohibited from performing financial calculations. All math is computed deterministically in Python.
2. **Prompt Injection Defense:** Dual delimiter fencing (`<<<USER_INPUT>>>`) and AST regex filtering prevent hostile instruction overrides.
3. **Zero Sensitive PII:** Client PAN, bank account numbers, and employee names are redacted prior to local prompt construction.
