import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Determine database path. For an offline desktop app, store it in a 'data' folder.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_PATH = os.path.join(DATA_DIR, 'finauditpro.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Setup SQLAlchemy Engine and Session
engine = create_engine(DATABASE_URL, echo=False)

from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in the database if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Provide a transactional session. Useful as a context manager or generator."""
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        pass # In desktop apps, we often manage closing manually per window, or use a context manager
