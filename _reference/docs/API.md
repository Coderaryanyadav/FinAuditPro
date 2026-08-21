# FinAuditPro — API & Service Reference Manual

FinAuditPro exposes two interface layers: an **In-Process Python Service Layer** used directly by the PySide6 desktop client, and a **FastAPI REST API Server (`/api/v1`)** for multi-user client-server deployments.

---

## 1. FastAPI REST API (`/api/v1`)

### Authentication & Headers

- **Authentication Scheme**: HTTP Bearer JWT (`Authorization: Bearer <access_token>`)
- **Algorithm**: HS256 (signed using environment/installation key `jwt_secret`)
- **Claims**: Includes `sub` (User ID), `username`, `role`, `exp` (expiration), and standard RFC 7519 `jti` (unique cryptographic token ID to prevent revocation collisions).
- **CORS Policy**: Configured in `api/main.py`. Disallows wildcard `*` origins when credentials are enabled.

---

### Endpoint Reference

| Group | Method | Endpoint | Description | Required Role / Permission |
|---|---|---|---|---|
| **Health** | `GET` | `/health` | Server health check | Public |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate user & issue JWT bearer token | Public |
| **Auth** | `POST` | `/api/v1/auth/logout` | Revoke active JWT token | Authenticated User |
| **Clients** | `GET` | `/api/v1/clients` | List all client engagements | `VIEW_DASHBOARD` / `MANAGE_CLIENTS` |
| **Clients** | `POST` | `/api/v1/clients` | Create a new client entity | `MANAGE_CLIENTS` |
| **Documents** | `GET` | `/api/v1/documents` | List uploaded audit documents | `UPLOAD_DOCUMENTS` |
| **Documents** | `POST` | `/api/v1/documents/upload` | Upload & ingest audit file (PDF/Excel) | `UPLOAD_DOCUMENTS` |
| **Working Papers**| `GET` | `/api/v1/working-papers` | List active working paper index | `EDIT_WORKING_PAPERS` |
| **Working Papers**| `POST` | `/api/v1/working-papers` | Create new indexed working paper | `EDIT_WORKING_PAPERS` |
| **Dashboard** | `GET` | `/api/v1/dashboard/metrics` | Retrieve real-time SQL dashboard KPIs | `VIEW_DASHBOARD` |
| **Dashboard** | `GET` | `/api/v1/dashboard/audit-logs` | Retrieve immutable audit trail logs | `VIEW_AUDIT_LOGS` |
| **Projects** | `POST` | `/api/v1/audit-projects/{id}/approve` | Statutory approval of audit project | `APPROVE_AUDIT` |

---

## 2. In-Process Python Service Layer (`src/services`)

### Core Services

#### `AuthenticationService`
- **Location**: `src/services/auth_service.py`
- **Methods**:
  - `login(username, password)` $\rightarrow$ `SessionToken`
  - `logout()` $\rightarrow$ `bool`
  - `verify_password(plain, hashed)` $\rightarrow$ `bool`
  - `handle_failed_attempt(username)` $\rightarrow$ Enforces 5-attempt lockout lockout window.

#### `ClientService`
- **Location**: `src/services/client_service.py`
- **Methods**:
  - `create_client(name, gst_number, pan, industry)` $\rightarrow$ `Client`
  - `list_clients()` $\rightarrow$ `List[Client]`
  - Enforces `MANAGE_CLIENTS` permission gate via `SecurityManager`.

#### `DocumentService`
- **Location**: `src/services/document_service.py`
- **Methods**:
  - `upload_document(file_path, client_id, engagement_id)` $\rightarrow$ `Document`
  - Runs magic-byte header validation, PyPDF/OCR parsing, and vector indexing.

#### `WorkingPaperService`
- **Location**: `src/services/working_paper_service.py`
- **Methods**:
  - `create_index(engagement_id, index_code, title)` $\rightarrow$ `WorkingPaperIndex`
  - `attach_document(index_id, document_id)`

---

## 3. RBAC Permission Matrix

| Permission Enum | Granted Roles |
|---|---|
| `VIEW_DASHBOARD` | All Roles |
| `MANAGE_CLIENTS` | `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER` |
| `UPLOAD_DOCUMENTS` | `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER`, `SENIOR_AUDITOR`, `ARTICLED_ASSISTANT` |
| `DELETE_DOCUMENTS` | `ADMINISTRATOR`, `AUDIT_PARTNER` |
| `RUN_AI_ANALYSIS` | `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER`, `SENIOR_AUDITOR` |
| `MANAGE_RULES` | `ADMINISTRATOR`, `AUDIT_PARTNER` |
| `EDIT_WORKING_PAPERS` | `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER`, `SENIOR_AUDITOR`, `ARTICLED_ASSISTANT` |
| `REVIEW_WORKING_PAPERS`| `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER` |
| `APPROVE_AUDIT` | `ADMINISTRATOR`, `AUDIT_PARTNER` |
| `GENERATE_REPORTS` | `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER`, `SENIOR_AUDITOR` |
| `SIGN_REPORTS` | `ADMINISTRATOR`, `AUDIT_PARTNER` |
| `VIEW_AUDIT_LOGS` | `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER` |
| `VIEW_ANALYTICS` | `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER`, `SENIOR_AUDITOR` |
| `MANAGE_SETTINGS` | `ADMINISTRATOR` |
| `PERFORM_BACKUP` | `ADMINISTRATOR` |

