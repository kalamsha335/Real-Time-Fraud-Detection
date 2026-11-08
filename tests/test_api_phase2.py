import unittest
import json
import os
import sys
import uuid

# Ensure root directory is on python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.services.model_service import ModelService
from api.schemas import PredictionRequest, AlertReviewUpdate, ReviewStatus
from fastapi import HTTPException


class TestPhase2PredictionAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.service = ModelService.get_instance()
        sample_path = os.path.join(os.path.dirname(__file__), "sample_transaction.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            cls.sample_data = json.load(f)

    def test_01_health_and_model_loading(self):
        health = self.service.get_health()
        self.assertEqual(health.status, "healthy")
        self.assertTrue(health.model_loaded)
        self.assertEqual(health.features_expected, 432)
        self.assertEqual(health.threshold, 0.5)

    def test_02_model_info(self):
        info = self.service.get_model_info()
        self.assertEqual(info.classifier, "XGBClassifier")
        self.assertEqual(info.expected_feature_count, 432)
        self.assertEqual(len(info.features), 432)

    def test_03_predict_missing_features_error(self):
        with self.assertRaises(HTTPException) as ctx:
            self.service.predict(
                transaction_data={"TransactionAmt": 25.0, "ProductCD": "W"},
                transaction_id=f"TX-INV-{uuid.uuid4().hex[:6]}"
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("missing_features", ctx.exception.detail)
        self.assertEqual(ctx.exception.detail["missing_count"], 430)

    def test_04_successful_prediction_and_alert_generation(self):
        dynamic_tx_id = f"TX-PHASE2-{uuid.uuid4().hex[:8]}"
        pred_res = self.service.predict(
            transaction_data=self.sample_data,
            transaction_id=dynamic_tx_id
        )
        self.assertEqual(pred_res.transaction_id, dynamic_tx_id)
        self.assertIsInstance(pred_res.fraud_probability, float)
        self.assertIn(pred_res.prediction, [0, 1])
        self.assertIn(pred_res.risk_level, ["LOW", "MEDIUM", "HIGH"])
        self.assertGreater(pred_res.inference_latency_ms, 0.0)

    def test_05_transactions_retrieval_and_filtering(self):
        txs = self.service.get_recent_transactions(limit=10)
        self.assertGreater(len(txs), 0)
        first_tx = txs[0]
        self.assertIsNotNone(first_tx.transaction_id)
        self.assertIsNotNone(first_tx.amount)

        # Risk level filter
        high_risk_txs = self.service.get_recent_transactions(risk_level="HIGH")
        for tx in high_risk_txs:
            self.assertEqual(tx.risk_level, "HIGH")

    def test_06_alerts_retrieval_and_analyst_review(self):
        # Create fresh transaction and alert
        tx_id = f"TX-ALERT-TEST-{uuid.uuid4().hex[:8]}"
        self.service.predict(self.sample_data, transaction_id=tx_id)

        pending_alerts = self.service.get_alerts(limit=10, review_status="PENDING")
        self.assertGreater(len(pending_alerts), 0)
        target_alert = pending_alerts[0]
        self.assertEqual(target_alert.review_status, "PENDING")

        # Update analyst review status
        updated = self.service.update_alert_review(
            alert_id=target_alert.alert_id,
            review_status=ReviewStatus.CONFIRMED_FRAUD.value,
            notes="Confirmed suspicious card behavior",
            reviewed_by="senior_analyst_42"
        )
        self.assertEqual(updated.review_status, "CONFIRMED_FRAUD")
        self.assertIn("senior_analyst_42", updated.analyst_notes)

    def test_07_system_metrics_calculation(self):
        metrics = self.service.get_metrics()
        self.assertGreaterEqual(metrics.total_transactions, 1)
        self.assertGreaterEqual(metrics.fraud_detection_rate, 0.0)
        self.assertEqual(
            metrics.total_transactions,
            metrics.fraudulent_detected + metrics.legitimate_transactions
        )
        self.assertGreater(metrics.uptime_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
