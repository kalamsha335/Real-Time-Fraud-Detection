import os
import sys
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.connection import engine, SessionLocal, Base, check_db_connection
from database.repository import DatabaseRepository
import database.models  # Registers all SQLAlchemy models

logger = logging.getLogger("init_db")
logging.basicConfig(level=logging.INFO)


def init_db():
    """Create all schema tables and seed baseline model metadata."""
    connected, status, dialect = check_db_connection()
    logger.info("Database connection status: %s (Dialect: %s)", status, dialect)

    logger.info("Creating database tables if not present...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully: %s", list(Base.metadata.tables.keys()))

    # Seed model metadata
    db = SessionLocal()
    try:
        meta = DatabaseRepository.seed_model_metadata(
            db=db,
            model_name="XGBoost Fraud Classification Pipeline",
            classifier="XGBClassifier",
            threshold=0.5,
            features_count=432,
            roc_auc=0.9086,
            pr_auc=0.5189,
            precision=0.22,
            recall=0.73
        )
        logger.info("Seeded model metadata: ID=%s, Model=%s, ROC-AUC=%.4f", meta.id, meta.model_name, meta.roc_auc)
    finally:
        db.close()

    return True


if __name__ == "__main__":
    init_db()
