# Engagement & Workspace Management

FinAuditPro organizes all audit workflows under a 3-tier hierarchy: **Firm $\rightarrow$ Client $\rightarrow$ Engagement**.

---

## 1. Hierarchy & Entities

```text
Audit Firm (FRN, PAN, GSTIN, Address)
  └── Client (CIN/LLPIN, PAN, GSTIN, Industry)
        └── Engagement (Financial Year, Audit Type, Lead Partner, Status)
```

- **Firm**: The statutory audit practice entity.
- **Client**: The audited company or entity.
- **Engagement**: A single statutory audit exercise for a specific financial year (e.g. `FY 2024-25`).

---

## 2. Multi-Tenant Engagement Isolation

Every piece of audit evidence, document page, financial row, risk assessment, finding, working paper, and report is strictly partitioned by `engagement_id`. Cross-engagement queries are blocked at the repository and SQL layer.

---

## 3. Application Services & Endpoints

- **`FirmService`** (`src/finauditpro/application/services/firm_service.py`):
  - `create_firm(dto: CreateFirmDTO) -> Firm`
  - `get_firm_by_id(firm_id: str) -> Firm | None`
  - `list_firms() -> list[Firm]`
- **`ClientService`** (`src/finauditpro/application/services/client_service.py`):
  - `create_client(dto: CreateClientDTO) -> Client`
  - `list_clients_for_firm(firm_id: str) -> list[Client]`
- **`EngagementService`** (`src/finauditpro/application/services/engagement_service.py`):
  - `create_engagement(dto: CreateEngagementDTO) -> Engagement`
  - `list_engagements_for_client(client_id: str) -> list[Engagement]`
  - `get_engagement_by_id(engagement_id: str) -> Engagement | None`
