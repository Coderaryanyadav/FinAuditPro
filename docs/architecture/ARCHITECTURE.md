# FinAuditPro — System Architecture & Design Specification

## 1. Architectural Philosophy & Layered DDD Structure
**FinAuditPro** is built strictly around Domain-Driven Design (DDD) principles with four decoupled architectural tiers:

```
+-------------------------------------------------------------------+
|                     PRESENTATION LAYER (PyQt6)                    |
|   Screens, ViewModels, Dialogs, State Coordinators, QSS Tokens    |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                     APPLICATION SERVICE LAYER                     |
|   Use Cases, Orchestrators, Unit of Work, Transaction Handlers    |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        DOMAIN CORE LAYER                          |
|   Entities, Value Objects, Domain Invariants, Integer Math Rules   |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                   INFRASTRUCTURE & PERSISTENCE                    |
|   SQLite WAL Repositories, Triggers, Crypto, LM Studio HTTP Client|
+-------------------------------------------------------------------+
```

## 2. Invariant Rules Governing Layer Boundaries
1. **Domain Isolation:** The `domain` layer has zero dependencies on external frameworks, UI libraries (PyQt6), or database drivers (SQLite). All business logic is pure Python.
2. **Deterministic Arithmetic:** All currency values are encapsulated in `Money` / integer paise value objects. No IEEE 754 floating-point arithmetic is permitted in domain entities.
3. **Immutability of Audit Trails:** Working paper status transitions, sign-offs, and audit logs are governed by SQLite database-level triggers and append-only tables.
4. **Offline Local Boundaries:** Outbound cloud networking is strictly prohibited. The local AI copilot communicates strictly over localhost loopback (`127.0.0.1:1234`) to LM Studio.

## 3. Structural Domain Relationship Graph

```
[Firm]
  │
  └── [Client]
        │
        └── [Engagement] ─── (Aggregate Root)
              ├── [EngagementMember] (RBAC Roles: Partner/Manager/Senior/Assistant)
              ├── [MaterialityBenchmark] (OM, PM, CTT thresholds)
              ├── [TrialBalance] ─── [TrialBalanceLineItem]
              │         │
              │         └── [AccountMapping] ─── [LeadSchedule]
              │                   │
              │                   └── [AdjustmentEntry] ─── [AdjustedTrialBalance]
              ├── [AuditProcedure] ─── [SamplingExecution]
              │         │
              │         └── [WorkingPaper] ─── [EvidenceLink] ─── [Document]
              │                   │
              │                   └── [ReviewNote] (Threaded notes & resolutions)
              ├── [AuditFinding] (Misstatements, CARO 2020 clauses, Form 3CD clauses)
              └── [AuditReport] ─── [UDINRecord] ─── [SealedArchiveManifest]
```
