import os
import platform
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base


def _get_app_data_dir() -> str:
    """
    Resolve a user-writable data directory per platform.

    On Windows this avoids writing into read-only C:\\Program Files\\ when
    the application is installed via Inno Setup / NSIS for standard (non-admin)
    domain users.  Falls back to the legacy relative path only when the
    environment variable is absent (e.g. during pytest).
    """
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    app_dir = os.path.join(base, "FinAuditPro")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


# Determine database path — always in a user-writable location.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = _get_app_data_dir()

DB_PATH = os.path.join(DATA_DIR, 'finauditpro.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Setup SQLAlchemy Engine and Session
engine = create_engine(DATABASE_URL, echo=False, connect_args={'timeout': 30.0})

from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000") # 64MB cache for M4 Pro high memory bandwidth
    cursor.execute("PRAGMA mmap_size=30000000000") # Memory mapped I/O
    cursor.execute("PRAGMA temp_store=MEMORY") # Keep temp tables in RAM
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in the database if they don't exist and run migrations."""
    from deployment.migration import DatabaseMigrator
    Base.metadata.create_all(bind=engine)
    DatabaseMigrator.migrate(DB_PATH)

from contextlib import contextmanager

@contextmanager
def get_session():
    """Provide a transactional session context manager that guarantees closing."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
