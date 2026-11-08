import os
import logging
from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("db_connection")
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Build Postgres URL from individual env vars or single DATABASE_URL
raw_pg_url = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'fraud_detection')}"
)

# Normalize postgresql:// to postgresql+psycopg2:// if psycopg2 is used
if raw_pg_url.startswith("postgresql://") and not raw_pg_url.startswith("postgresql+"):
    DEFAULT_POSTGRES_URL = raw_pg_url.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    DEFAULT_POSTGRES_URL = raw_pg_url

SQLITE_FALLBACK_URL = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'fraud_detection.db')}"

ACTIVE_DB_URL = DEFAULT_POSTGRES_URL
engine = None
is_postgres = False

try:
    # Attempt to test connection to configured database
    test_engine = create_engine(
        ACTIVE_DB_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3} if "postgresql" in ACTIVE_DB_URL else {}
    )
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine = test_engine
    is_postgres = "postgresql" in ACTIVE_DB_URL
    logger.info("Connected successfully to database: %s", ACTIVE_DB_URL.split("@")[-1] if "@" in ACTIVE_DB_URL else ACTIVE_DB_URL)
except Exception as e:
    logger.warning("Could not establish direct connection to configured database (%s). Error: %s", ACTIVE_DB_URL, e)
    logger.info("Falling back to local SQLite database for standalone development and testing: %s", SQLITE_FALLBACK_URL)
    ACTIVE_DB_URL = SQLITE_FALLBACK_URL
    engine = create_engine(
        ACTIVE_DB_URL,
        connect_args={"check_same_thread": False}
    )
    is_postgres = False

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """Dependency that yields database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, str, str]:
    """Check database health, dialect, and status."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        dialect = "PostgreSQL" if is_postgres else "SQLite (Fallback/Local)"
        return True, "connected", dialect
    except Exception as err:
        return False, str(err), "unknown"
