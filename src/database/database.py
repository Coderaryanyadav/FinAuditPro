import os
import platform
import logging
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from .models import Base
from core.config import config

logger = logging.getLogger(__name__)

# Detect SQLCipher driver if installed
HAS_SQLCIPHER = False
sqlcipher_module = None

try:
    import sqlcipher3 as sqlcipher_module
    HAS_SQLCIPHER = True
except ImportError:
    try:
        from pysqlcipher3 import dbapi2 as sqlcipher_module
        HAS_SQLCIPHER = True
    except ImportError:
        HAS_SQLCIPHER = False
        sqlcipher_module = None


def _get_app_data_dir() -> str:
    """Resolve a user-writable data directory per platform."""
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


DATA_DIR = config.data_dir
DB_PATH = os.path.join(DATA_DIR, 'finauditpro.db')

# Resolve database URL: prioritize environment/config override (e.g. PostgreSQL)
if config.database_url:
    DATABASE_URL = config.database_url
elif HAS_SQLCIPHER:
    DATABASE_URL = f"sqlite+pysqlcipher:///{DB_PATH}"
else:
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    logger.warning("sqlcipher3 library not available. Live database running in standard plain SQLite mode.")


def get_db_encryption_key() -> str:
    """Derive hex encryption passphrase for SQLCipher engine."""
    try:
        from security.crypto import _get_or_create_installation_key
        return _get_or_create_installation_key(DATA_DIR).hex()
    except Exception:
        return "finauditpro_default_db_key"


is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite and HAS_SQLCIPHER and sqlcipher_module:
    passphrase = get_db_encryption_key()
    def _creator():
        conn = sqlcipher_module.connect(DB_PATH)
        conn.execute(f"PRAGMA key = '{passphrase}'")
        return conn
    engine = create_engine(DATABASE_URL, echo=False, creator=_creator, connect_args={'timeout': 30.0})
else:
    connect_args = {'timeout': 30.0} if is_sqlite else {}
    engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if is_sqlite:
        cursor = dbapi_connection.cursor()
        if HAS_SQLCIPHER:
            try:
                passphrase = get_db_encryption_key()
                cursor.execute(f"PRAGMA key = '{passphrase}'")
            except Exception:
                pass
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA mmap_size=30000000000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables in the database if they don't exist and run migrations."""
    from deployment.migration import DatabaseMigrator
    Base.metadata.create_all(bind=engine)
    if is_sqlite and os.path.exists(DB_PATH):
        DatabaseMigrator.migrate(DB_PATH)


from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError


@contextmanager
def get_session():
    """Provide a transactional session context manager that guarantees closing."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except (SQLAlchemyError, OSError) as e:
        session.rollback()
        raise e
    finally:
        session.close()
