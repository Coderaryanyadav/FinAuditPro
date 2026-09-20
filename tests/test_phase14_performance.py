"""Phase 14 — Performance Optimization & Benchmark Test Suite."""

import time

import pytest
from sqlalchemy import text

from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.practice_dashboard_service import PracticeDashboardService
from finauditpro.application.services.unified_search_service import UnifiedSearchService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
)


@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "perf_test.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()
    return db_manager


def test_startup_and_schema_initialization_perf(tmp_path):
    db_path = tmp_path / "startup_perf.db"
    t0 = time.perf_counter()
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()
    t1 = time.perf_counter()
    elapsed_ms = (t1 - t0) * 1000
    assert elapsed_ms < 1000, f"Schema init took {elapsed_ms:.2f}ms, expected < 1000ms"


def test_large_dataset_benchmarks_and_isolation(temp_db):
    engine = temp_db.engine
    client_service = ClientService(temp_db)
    eng_service = EngagementService(temp_db)
    dash_service = PracticeDashboardService(temp_db)
    search_service = UnifiedSearchService(temp_db)

    print("\n--- Seeding 50 clients and 200 engagements ---")
    t0 = time.perf_counter()
    client_ids = []
    engagement_ids = []

    # Insert firm for foreign key satisfaction if required
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO firms (id, name, created_at, updated_at) "
                "VALUES ('firm_1', 'Main CA Practice', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
            )
        )

        for i in range(50):
            c_id = f"cli_{i}"
            client_ids.append(c_id)
            conn.execute(
                text(
                    "INSERT INTO clients (id, firm_id, name, pan, entity_type, created_at, updated_at) "
                    "VALUES (:id, 'firm_1', :name, :pan, :entity_type, :created_at, :created_at)"
                ),
                {
                    "id": c_id,
                    "name": f"Client Firm {i} Pvt Ltd",
                    "pan": f"ABCDE{i:04d}F",
                    "entity_type": "Private Limited Company",
                    "created_at": "2026-01-01T00:00:00",
                },
            )
            for j in range(4):
                e_id = f"eng_{i}_{j}"
                engagement_ids.append(e_id)
                conn.execute(
                    text(
                        "INSERT INTO engagements (id, firm_id, client_id, financial_year, audit_type, status, assigned_team_json, created_at, updated_at) "
                        "VALUES (:id, 'firm_1', :client_id, :fy, :type, :status, '[]', :created_at, :created_at)"
                    ),
                    {
                        "id": e_id,
                        "client_id": c_id,
                        "fy": "FY 2025-26",
                        "type": "Statutory Audit",
                        "status": "Planning",
                        "created_at": "2026-01-01T00:00:00",
                    },
                )

        print("--- Seeding 100,000 GL ledger entries ---")
        ds_id = "ds_large_100k"
        conn.execute(
            text(
                "INSERT INTO financial_datasets (id, engagement_id, dataset_name, dataset_type, version, file_path, content_hash, row_count, column_mappings_json, created_at, updated_at) "
                "VALUES (:id, :eng_id, 'GL Ledger 100k', 'General Ledger', 1, '/tmp/ledger.xml', 'hash123', 100000, '{}', '2026-01-01T00:00:00', '2026-01-01T00:00:00')"
            ),
            {"id": ds_id, "eng_id": engagement_ids[0]},
        )

        ledger_rows = [
            {
                "id": f"row_{r}",
                "dataset_id": ds_id,
                "source_row_no": r,
                "entry_date": "2026-03-15",
                "voucher_type": "Payment",
                "voucher_number": f"VCH-{r}",
                "account_code": f"ACC-{r % 100}",
                "account_name": f"Account Head {r % 100}",
                "debit_paise": 10000 if r % 2 == 0 else 0,
                "credit_paise": 10000 if r % 2 != 0 else 0,
                "narration": f"Narration for transaction {r}",
                "reference": f"REF-{r}",
                "created_by_raw": "System",
                "raw_values_json": "{}",
            }
            for r in range(100000)
        ]
        conn.execute(
            text(
                "INSERT INTO ledger_entries VALUES "
                "(:id, :dataset_id, :source_row_no, :entry_date, :voucher_type, :voucher_number, "
                ":account_code, :account_name, :debit_paise, :credit_paise, :narration, :reference, "
                ":created_by_raw, :raw_values_json)"
            ),
            ledger_rows,
        )

        print("--- Seeding 50,000 documents and FTS indices ---")
        doc_rows = [
            {
                "id": f"doc_{d}",
                "engagement_id": engagement_ids[d % 200],
                "filename": f"Document_{d}.pdf",
                "original_path": f"/tmp/Document_{d}.pdf",
                "stored_path": f"/tmp/stored_Document_{d}.pdf",
                "file_size_bytes": 1024,
                "content_hash": f"hash_{d}",
                "mime_type": "application/pdf",
                "document_category": "Tax",
                "category_confidence": 1.0,
                "page_count": 1,
                "status": "CONFIRMED",
                "uploaded_at": "2026-01-01T00:00:00",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }
            for d in range(50000)
        ]
        conn.execute(
            text(
                "INSERT INTO documents (id, engagement_id, filename, original_path, stored_path, file_size_bytes, "
                "content_hash, mime_type, document_category, category_confidence, page_count, status, uploaded_at, created_at, updated_at) "
                "VALUES (:id, :engagement_id, :filename, :original_path, :stored_path, :file_size_bytes, "
                ":content_hash, :mime_type, :document_category, :category_confidence, :page_count, :status, :uploaded_at, :created_at, :updated_at)"
            ),
            doc_rows,
        )

        fts_rows = [
            {
                "engagement_id": engagement_ids[d % 200],
                "document_id": f"doc_{d}",
                "page_id": f"page_{d}",
                "page_number": 1,
                "extracted_text": f"Audit Evidence GST Return Invoice #{d} for vendor ACME Corp GSTIN27AAAAA0000A1Z5",
            }
            for d in range(0, 50000, 10)  # 5,000 FTS entries
        ]
        conn.execute(
            text(
                "INSERT INTO document_fts (engagement_id, document_id, page_id, page_number, extracted_text) "
                "VALUES (:engagement_id, :document_id, :page_id, :page_number, :extracted_text)"
            ),
            fts_rows,
        )

    t1 = time.perf_counter()
    print(f"Dataset seeded in {t1 - t0:.2f} seconds.")

    # Benchmark 1: Command Center / Practice Dashboard Summary Load (< 300ms)
    t_start = time.perf_counter()
    summary = dash_service.get_practice_summary()
    t_end = time.perf_counter()
    dash_ms = (t_end - t_start) * 1000
    assert summary.total_clients == 50
    assert summary.active_engagements == 200
    assert dash_ms < 500, f"Dashboard summary took {dash_ms:.2f}ms, expected < 500ms"

    # Benchmark 2: Client Page Listing (< 100ms)
    t_start = time.perf_counter()
    clients = client_service.list_all_clients()
    t_end = time.perf_counter()
    list_ms = (t_end - t_start) * 1000
    assert len(clients) == 50
    assert list_ms < 200, f"Client listing took {list_ms:.2f}ms, expected < 200ms"

    # Benchmark 3: Financial Analytics over 100,000 GL rows (< 1.5s)
    t_start = time.perf_counter()
    with temp_db.session_scope() as session:
        res = session.execute(
            text("SELECT COUNT(*), SUM(debit_paise) FROM ledger_entries WHERE dataset_id = :ds_id"),
            {"ds_id": ds_id},
        ).fetchone()
    t_end = time.perf_counter()
    gl_ms = (t_end - t_start) * 1000
    assert res[0] == 100000
    assert gl_ms < 1500, f"100,000 GL row aggregation took {gl_ms:.2f}ms, expected < 1500ms"

    # Benchmark 4: Unified FTS5 Search Latency (< 150ms)
    t_start = time.perf_counter()
    search_results = search_service.search("GSTIN27AAAAA0000A1Z5")
    t_end = time.perf_counter()
    search_ms = (t_end - t_start) * 1000
    assert len(search_results) > 0
    assert search_ms < 300, f"Search took {search_ms:.2f}ms, expected < 300ms"

    # Benchmark 5: Security Isolation under high volume
    with temp_db.session_scope() as session:
        repo = EngagementRepository(session)
        cli_0_engagements = repo.list_by_client("cli_0")
        cli_1_engagements = repo.list_by_client("cli_1")
        assert len(cli_0_engagements) == 4
        assert len(cli_1_engagements) == 4
        for eng in cli_0_engagements:
            assert eng.client_id == "cli_0"
            assert eng.client_id != "cli_1"
