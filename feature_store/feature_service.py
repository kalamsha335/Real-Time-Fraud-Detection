import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from feast import FeatureStore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from feature_store.generate_features import build_card_features_parquet

logger = logging.getLogger("feast_service")
logging.basicConfig(level=logging.INFO)

REPO_PATH = os.path.join(BASE_DIR, "feature_store", "feature_repo")


class FeastFeatureService:
    """Manages Feast feature store initialization, materialization, and retrieval."""

    def __init__(self, repo_path: str = REPO_PATH):
        self.repo_path = repo_path
        self._ensure_parquet_source()
        self.store = FeatureStore(repo_path=self.repo_path)

    def _ensure_parquet_source(self):
        """Ensures data/card_features.parquet exists."""
        parquet_path = os.path.join(self.repo_path, "data", "card_features.parquet")
        if not os.path.exists(parquet_path):
            logger.info("Card features parquet not found. Generating...")
            build_card_features_parquet(sample_size=3000)

    def apply_definitions(self):
        """Register entities and feature views in registry."""
        from feature_store.feature_repo.features import card_entity, card_features_view
        logger.info("Applying Feast definitions to registry...")
        self.store.apply([card_entity, card_features_view])

    def materialize_online_store(self, end_date: Optional[datetime] = None):
        """Materializes latest features to SQLite online store for real-time inference."""
        self.apply_definitions()
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        target_end = end_date or datetime.now(timezone.utc) + timedelta(days=365)
        logger.info("Materializing features from %s to %s...", start_date, target_end)
        self.store.materialize(start_date=start_date, end_date=target_end)
        logger.info("Materialization complete.")

    def get_online_features(self, card1: int) -> Dict[str, Any]:
        """
        Sub-millisecond retrieval of online features for an incoming transaction.
        """
        feature_refs = [
            "card_features:card1_avg_amount",
            "card_features:card1_trans_count_24h",
            "card_features:card1_total_count",
            "card_features:card1_max_amount"
        ]
        entity_rows = [{"card1": int(card1)}]
        response = self.store.get_online_features(
            features=feature_refs,
            entity_rows=entity_rows
        ).to_dict()

        # Simplify dictionary
        return {
            "card1": card1,
            "card1_avg_amount": response.get("card1_avg_amount", [None])[0],
            "card1_trans_count_24h": response.get("card1_trans_count_24h", [None])[0],
            "card1_total_count": response.get("card1_total_count", [None])[0],
            "card1_max_amount": response.get("card1_max_amount", [None])[0],
        }

    def get_historical_features(self, entity_df: pd.DataFrame) -> pd.DataFrame:
        """
        Point-in-time correct join for model training and historical validation,
        guaranteeing zero future data leakage.
        """
        feature_refs = [
            "card_features:card1_avg_amount",
            "card_features:card1_trans_count_24h",
            "card_features:card1_total_count",
            "card_features:card1_max_amount"
        ]
        training_data = self.store.get_historical_features(
            entity_df=entity_df,
            features=feature_refs
        )
        return training_data.to_df()


if __name__ == "__main__":
    service = FeastFeatureService()
    service.materialize_online_store()
    features = service.get_online_features(card1=13926)
    print("Online features for card1=13926:", features)
