"""Database configuration and session management for SQLite persistence."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

APP_NAME = "FinAuditPro"


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""

    pass


def get_default_db_path() -> Path:
    """Return default database file path in native platform data directory."""
    app_data = os.environ.get("FINAUDITPRO_DATA_DIR")
    if app_data:
        data_dir = Path(app_data) / "db"
    else:
        data_dir = Path.home() / ".gemini" / "antigravity-ide" / "app_data" / "db"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "finauditpro.db"


def create_sqlite_engine(db_path: Path | str | None = None, echo: bool = False) -> Engine:
    """Create a configured SQLite engine with WAL mode and foreign keys enabled."""
    if db_path is None:
        db_path = get_default_db_path()
    elif isinstance(db_path, str):
        db_path = Path(db_path)

    if db_path != Path(":memory:"):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    connection_url = f"sqlite:///{db_path}"
    engine = create_engine(
        connection_url,
        echo=echo,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


class DatabaseManager:
    """Manages database connection lifecycle and session creation."""

    def __init__(self, db_path: Path | str | None = None, echo: bool = False) -> None:
        self.db_path = str(db_path) if db_path else str(get_default_db_path())
        self.engine = create_sqlite_engine(db_path=db_path, echo=echo)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def create_tables(self) -> None:
        """Create all tables in database and apply append-only triggers for audit_events."""
        import finauditpro.infrastructure.persistence.models  # noqa: F401
        Base.metadata.create_all(self.engine)
        self._ensure_columns()
        self._create_fts_tables()
        self._create_audit_triggers()

    def _ensure_columns(self) -> None:
        """Safely add missing schema columns to pre-existing SQLite tables."""
        with self.engine.begin() as conn:
            for table_name, table in Base.metadata.tables.items():
                try:
                    res = conn.execute(text(f"PRAGMA table_info({table_name});")).fetchall()
                    if not res:
                        continue
                    existing_cols = {row[1] for row in res}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            col_type = col.type.compile(self.engine.dialect)
                            default_clause = ""
                            sd = getattr(col, "server_default", None)
                            if sd is not None and hasattr(sd, "arg"):
                                default_clause = f" DEFAULT {sd.arg}"
                            else:
                                cd = getattr(col, "default", None)
                                if cd is not None and hasattr(cd, "arg") and not callable(cd.arg):
                                    val = cd.arg
                                    default_clause = f" DEFAULT '{val}'" if isinstance(val, str) else f" DEFAULT {val}"

                            stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause};"
                            conn.execute(text(stmt))
                except Exception:
                    pass



    def _create_fts_tables(self) -> None:
        """Create SQLite FTS5 virtual tables for document full-text search."""
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
                    engagement_id UNINDEXED,
                    document_id UNINDEXED,
                    page_id UNINDEXED,
                    page_number UNINDEXED,
                    extracted_text,
                    tokenize='unicode61'
                );
            """)
            )

    def _create_audit_triggers(self) -> None:
        """Create SQLite triggers rejecting UPDATE and DELETE on audit_events table if present."""
        with self.engine.begin() as conn:
            # Check if audit_events table exists
            res = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_events'")
            ).fetchone()
            if not res:
                return
            conn.execute(
                text("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_events_update
                BEFORE UPDATE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'Audit events are append-only. UPDATE operations are prohibited.');
                END;
            """)
            )
            conn.execute(
                text("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_events_delete
                BEFORE DELETE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'Audit events are append-only. DELETE operations are prohibited.');
                END;
            """)
            )

    def drop_tables(self) -> None:
        """Drop all tables in database safely by turning off foreign key constraints during drop."""
        with self.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            Base.metadata.drop_all(conn)
            conn.execute(text("PRAGMA foreign_keys=ON"))

    def get_session(self) -> Session:
        """Return a new SQLAlchemy session."""
        return self.session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
