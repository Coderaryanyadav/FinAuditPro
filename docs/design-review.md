# FinAuditPro — Apple-Level Design Review & Human Interface Audit

This document details the visual, interaction, typography, and human interface design principles applied across **FinAuditPro**.

---

## 1. Visual Design Philosophy & Human Interface Principles

Target Posture: **Quiet Confidence, Extreme Precision, Visual Calm, Audit-Grade Trust**.

1. **Restraint & Less, But Better**:
   - Palette dominated by neutral dark layers (`#0f1117` base, `#181b22` card surface, `#222732` elevated surface, `#2a303c` borders).
   - Zero decorative 3D gradients, rainbow dashboards, or neon borders. Color is used strictly for semantic status, risk, and action indicators.
2. **Tabular Numeric Legibility**:
   - All financial figures, paise balances, materiality thresholds, and trial balance lines employ monospaced tabular typography for scanning.
3. **Categorized Navigation Architecture**:
   - Sidebar grouped into 4 intuitive audit sections: `AUDIT WORKSPACE`, `EVIDENCE & ANALYTICS`, `WORK & REVIEWS`, `OUTPUT & SYSTEM`.
4. **Subtle Micro-Interactions**:
   - Purposeful hover states, focus rings (`#38bdf8`), compact table cell padding, and immediate visual feedback without slow or distracting animations.

---

## 2. Component System Audit

- **`MetricCard`**: Left accent border (`#38bdf8`, `#f59e0b`, `#ef4444`) with uppercase quiet labels and prominent 22px bold metric values.
- **`StatusBadge`**: Semantic pill badges (`success`, `warning`, `danger`, `info`, `muted`) with 11px semi-bold text and subtle borders.
- **`CardWidget`**: 8px rounded corners with `#2a303c` subtle borders, eliminating floating card clutter.
- **`HeaderContextBar`**: Displays active context breadcrumb `Active: Firm ➔ Client ➔ Engagement (FY)` with explicit visual feedback.
