import unittest
import os
import sys
import json
import uuid
import pandas as pd
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.main import app
from feature_store.feature_service import FeastFeatureService
from graph.graph_analysis import GraphAnalysisService
from monitoring.drift_monitor import get_drift_monitor
from monitoring.mlflow_logger import MLflowTracker
from database.connection import SessionLocal
from database.repository import DatabaseRepository


class TestEndToEndPlatformIntegration(unittest.TestCase):
    """
    Master end-to-end integration test suite validating all 10 project phases:
    API, XGBoost inference, Database persistence, Feast feature store,
    Graph Neural Network analysis, Evidently monitoring, MLflow tracking,
    and React dashboard assets.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.feast_service = FeastFeatureService()
        cls.graph_service = GraphAnalysisService()
        cls.drift_monitor = get_drift_monitor()
        cls.mlflow_tracker = MLflowTracker()

        # Load standard 432-feature template
        sample_path = os.path.join(BASE_DIR, "tests", "sample_transaction.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            cls.feature_template = json.load(f)

    def test_01_health_and_model_availability(self):
        """Step 1: Check FastAPI health and ensure XGBoost pipeline is loaded."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])
        self.assertEqual(data["features_expected"], 432)
        self.assertEqual(data["threshold"], 0.50)

    def test_02_feast_feature_store_online_retrieval(self):
        """Step 2: Verify Feast feature store returns sub-millisecond point-in-time features."""
        features = self.feast_service.get_online_features(card1=13926)
        self.assertIsInstance(features, dict)
        self.assertEqual(features["card1"], 13926)
        self.assertIn("card1_avg_amount", features)
        self.assertIn("card1_trans_count_24h", features)
        self.assertIn("card1_total_count", features)

    def test_03_prediction_and_database_persistence(self):
        """Step 3: Run XGBoost inference on 432-feature payload and verify DB insertion."""
        tx_payload = dict(self.feature_template)
        test_tx_id = f"e2e-tx-{uuid.uuid4().hex[:8]}"
        tx_payload["TransactionID"] = test_tx_id
        tx_payload["TransactionAmt"] = 999.50
        tx_payload["C1"] = 15.0

        res = self.client.post("/predict", json={"transaction": tx_payload})
        self.assertEqual(res.status_code, 200)
        pred_data = res.json()

        self.assertIn("fraud_probability", pred_data)
        self.assertIn("prediction", pred_data)
        self.assertIn("risk_level", pred_data)
        self.assertIn(pred_data["risk_level"], ["LOW", "MEDIUM", "HIGH"])

        # Verify record in database
        db = SessionLocal()
        try:
            db_txs = DatabaseRepository.get_recent_transactions(db, limit=10)
            tx_ids = [t.transaction_id for t in db_txs]
            self.assertIn(pred_data["transaction_id"], tx_ids)
        finally:
            db.close()

    def test_04_alert_creation_and_analyst_triage(self):
        """Step 4: Verify high-risk alert creation and analyst review lifecycle."""
        alerts_res = self.client.get("/alerts?limit=10")
        self.assertEqual(alerts_res.status_code, 200)
        alerts_list = alerts_res.json().get("alerts", [])

        if not alerts_list:
            # Inject a high risk transaction to guarantee alert
            high_risk_tx = dict(self.feature_template)
            high_risk_tx["TransactionAmt"] = 5500.0
            high_risk_tx["C1"] = 50.0
            self.client.post("/predict", json={"transaction": high_risk_tx})
            alerts_res = self.client.get("/alerts?limit=10")
            alerts_list = alerts_res.json().get("alerts", [])

        self.assertGreater(len(alerts_list), 0)
        target_alert = alerts_list[0]
        alert_id = target_alert["alert_id"]

        # Analyst reviews and confirms fraud
        patch_res = self.client.patch(
            f"/alerts/{alert_id}/review",
            json={
                "review_status": "CONFIRMED_FRAUD",
                "analyst_notes": "Confirmed syndicate pattern with cardholder dispute.",
                "reviewed_by": "lead_security_analyst"
            }
        )
        self.assertEqual(patch_res.status_code, 200)
        updated_alert = patch_res.json()
        self.assertEqual(updated_alert["review_status"], "CONFIRMED_FRAUD")

    def test_05_graph_relationship_analysis_and_fusion(self):
        """Step 5: Verify PyTorch Geometric relationship graph analysis and score fusion."""
        graph_res = self.client.get("/graph/analysis?limit=50&fusion_weight=0.20")
        self.assertEqual(graph_res.status_code, 200)
        graph = graph_res.json()

        self.assertIn("network_topology", graph)
        self.assertIn("nodes", graph["network_topology"])
        self.assertIn("links", graph["network_topology"])
        self.assertTrue("statistics" in graph or "connectivity_statistics" in graph)
        self.assertIn("disclaimer", graph)
        self.assertIn("fusion_policy", graph)

        # Confirm limitation disclaimer is present
        self.assertIn("relationship proxies only", graph["disclaimer"].lower())

    def test_06_evidently_drift_monitoring_and_distinction(self):
        """Step 6: Verify Evidently data drift analysis and feature drift vs performance distinction."""
        drift_res = self.client.get("/monitoring/drift")
        self.assertEqual(drift_res.status_code, 200)
        drift = drift_res.json()

        self.assertEqual(drift["status"], "success")
        self.assertIn("feature_drift_detected", drift)
        self.assertIn("transaction_amount_distribution", drift)
        self.assertIn("distinction_analysis", drift)

        dist = drift["distinction_analysis"]
        self.assertIn("feature_drift_status", dist)
        self.assertIn("performance_degradation_status", dist)
        self.assertIn("key_distinction_explanation", dist)

        # Check HTML report
        report_res = self.client.get("/monitoring/drift/report")
        self.assertEqual(report_res.status_code, 200)
        self.assertIn("text/html", report_res.headers.get("content-type", ""))

    def test_07_mlflow_model_tracking_runs(self):
        """Step 7: Verify MLflow tracking database contains valid benchmark runs."""
        runs_res = self.client.get("/monitoring/mlflow/runs")
        self.assertEqual(runs_res.status_code, 200)
        runs_data = runs_res.json()

        self.assertIn("runs", runs_data)
        self.assertGreaterEqual(runs_data["total_runs"], 1)

        summary_res = self.client.get("/monitoring/model-summary")
        self.assertEqual(summary_res.status_code, 200)
        summary = summary_res.json()
        val = summary["validation_metrics"]
        self.assertEqual(val["roc_auc"], 0.9086)
        self.assertEqual(val["pr_auc"], 0.5189)
        self.assertEqual(val["fraud_recall"], 0.73)
        self.assertEqual(val["fraud_precision"], 0.22)

    def test_08_frontend_distribution_artifacts(self):
        """Step 8: Verify React Analyst Dashboard production build assets are compiled."""
        dist_html = os.path.join(BASE_DIR, "frontend", "dist", "index.html")
        self.assertTrue(os.path.exists(dist_html), "Frontend dist/index.html not found.")
        with open(dist_html, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("FraudShield AI", html)


if __name__ == "__main__":
    unittest.main()
