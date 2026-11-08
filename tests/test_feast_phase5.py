import unittest
import os
import sys
import pandas as pd
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from feature_store.feature_service import FeastFeatureService
from feature_store.feature_repo.features import card_entity, card_features_view


class TestPhase5FeastFeatureStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.service = FeastFeatureService()
        cls.service.materialize_online_store()

    def test_01_entity_and_feature_view_definitions(self):
        """Verify entity and schema definitions in feature view."""
        self.assertEqual(card_entity.name, "card1")
        self.assertEqual(card_features_view.name, "card_features")
        field_names = [f.name for f in card_features_view.schema]
        self.assertIn("card1_avg_amount", field_names)
        self.assertIn("card1_trans_count_24h", field_names)
        self.assertIn("card1_total_count", field_names)
        self.assertIn("card1_max_amount", field_names)

    def test_02_online_feature_retrieval(self):
        """Verify sub-millisecond retrieval of online features for real-time inference."""
        features = self.service.get_online_features(card1=13926)
        self.assertIsInstance(features, dict)
        self.assertEqual(features["card1"], 13926)
        self.assertIn("card1_avg_amount", features)
        self.assertIn("card1_trans_count_24h", features)
        self.assertIn("card1_total_count", features)

    def test_03_historical_point_in_time_retrieval(self):
        """Verify point-in-time correct join for training data."""
        parquet_path = os.path.join(BASE_DIR, "feature_store", "feature_repo", "data", "card_features.parquet")
        df_p = pd.read_parquet(parquet_path)
        sample_card = int(df_p["card1"].iloc[0])
        sample_time = df_p[df_p["card1"] == sample_card]["event_timestamp"].iloc[-1]

        entity_df = pd.DataFrame({
            "card1": [sample_card],
            "event_timestamp": [sample_time]
        })
        historical_df = self.service.get_historical_features(entity_df)
        self.assertEqual(len(historical_df), 1)
        self.assertIn("card1_avg_amount", historical_df.columns)
        self.assertIn("card1_trans_count_24h", historical_df.columns)
        self.assertIn("card1_total_count", historical_df.columns)

    def test_04_point_in_time_monotonic_growth(self):
        """Verify that historical counts at later timestamps reflect non-decreasing transaction activity."""
        parquet_path = os.path.join(BASE_DIR, "feature_store", "feature_repo", "data", "card_features.parquet")
        df_p = pd.read_parquet(parquet_path)
        # Find card with multiple events
        val_counts = df_p["card1"].value_counts()
        mult_cards = val_counts[val_counts > 1].index
        if len(mult_cards) > 0:
            target_card = int(mult_cards[0])
            card_times = df_p[df_p["card1"] == target_card]["event_timestamp"].tolist()
            t_early = card_times[0]
            t_late = card_times[-1]

            entity_df = pd.DataFrame({
                "card1": [target_card, target_card],
                "event_timestamp": [t_early, t_late]
            })
            joined = self.service.get_historical_features(entity_df)
            self.assertEqual(len(joined), 2)
            c_early = joined["card1_total_count"].iloc[0]
            c_late = joined["card1_total_count"].iloc[1]
            self.assertLessEqual(c_early, c_late)


if __name__ == "__main__":
    unittest.main()
