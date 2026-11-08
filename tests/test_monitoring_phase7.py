import unittest
import os
import sys
import pandas as pd
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.main import app
from monitoring.drift_monitor import get_drift_monitor, DriftMonitor
from monitoring.mlflow_logger import MLflowTracker


class TestPhase7MonitoringAndMLflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.monitor = get_drift_monitor()
        cls.tracker = MLflowTracker()

    def test_01_reference_baseline_generation(self):
        """Verify drift monitor generates and caches a valid reference baseline dataset."""
        df = self.monitor.reference_df
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreaterEqual(len(df), 100)
        self.assertIn("TransactionAmt", df.columns)
        self.assertIn("card1", df.columns)
        self.assertIn("fraud_probability", df.columns)
        self.assertIn("prediction", df.columns)

    def test_02_drift_analysis_execution(self):
        """Verify Evidently drift analysis returns expected structure and statistics."""
        res = self.monitor.run_drift_analysis(save_report=True)
        self.assertEqual(res["status"], "success")
        self.assertIn("feature_drift_detected", res)
        self.assertIn("drifted_features_count", res)
        self.assertIn("drift_share", res)
        self.assertIn("transaction_amount_distribution", res)
        self.assertIn("fraud_prediction_distribution", res)
        self.assertIn("distinction_analysis", res)

        amt_dist = res["transaction_amount_distribution"]
        self.assertIn("reference_mean", amt_dist)
        self.assertIn("current_mean", amt_dist)

    def test_03_distinguish_feature_drift_from_performance_degradation(self):
        """Verify critical requirement: explicit distinction between feature drift and performance degradation."""
        res = self.monitor.run_drift_analysis(save_report=False)
        dist = res["distinction_analysis"]

        self.assertIn("feature_drift_status", dist)
        self.assertIn("performance_degradation_status", dist)
        self.assertIn("key_distinction_explanation", dist)
        self.assertIn("ground_truth_labels_available", dist)
        # Check explanatory clarity
        self.assertIn("chargebacks", dist["key_distinction_explanation"].lower())

    def test_04_html_drift_report_generation(self):
        """Verify that Evidently generates a non-empty HTML report on disk."""
        self.assertTrue(os.path.exists(self.monitor.report_path))
        self.assertGreater(os.path.getsize(self.monitor.report_path), 500)

    def test_05_mlflow_tracker_runs_and_metrics(self):
        """Verify MLflow tracker reads existing historical runs and authentic validation metrics."""
        runs = self.tracker.get_runs()
        self.assertGreaterEqual(len(runs), 1)

        metrics = self.tracker.get_latest_metrics()
        self.assertEqual(metrics["roc_auc"], 0.9086)
        self.assertEqual(metrics["pr_auc"], 0.5189)
        self.assertEqual(metrics["precision"], 0.22)
        self.assertEqual(metrics["recall"], 0.73)

    def test_06_mlflow_safe_logging(self):
        """Verify new validation runs can be logged to MLflow without altering prior runs."""
        run_id = self.tracker.log_new_run(
            run_name="Monitoring_Validation_Check",
            params={"batch_size": 100, "threshold": 0.5},
            metrics={"test_roc_auc": 0.909, "test_pr_auc": 0.520},
            tags={"environment": "unit-test", "type": "drift-check"}
        )
        self.assertIsNotNone(run_id)
        self.assertIsInstance(run_id, str)

    def test_07_api_monitoring_endpoints(self):
        """Verify FastAPI endpoints for drift metrics, HTML report, MLflow runs, and model summary."""
        # 1. GET /monitoring/drift
        res = self.client.get("/monitoring/drift")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")

        # 2. GET /monitoring/drift/report
        res_html = self.client.get("/monitoring/drift/report")
        self.assertEqual(res_html.status_code, 200)
        self.assertIn("text/html", res_html.headers.get("content-type", ""))

        # 3. GET /monitoring/mlflow/runs
        res_runs = self.client.get("/monitoring/mlflow/runs")
        self.assertEqual(res_runs.status_code, 200)
        runs_data = res_runs.json()
        self.assertIn("runs", runs_data)
        self.assertGreaterEqual(runs_data["total_runs"], 1)

        # 4. GET /monitoring/model-summary
        res_sum = self.client.get("/monitoring/model-summary")
        self.assertEqual(res_sum.status_code, 200)
        summary = res_sum.json()
        self.assertEqual(summary["expected_features"], 432)
        self.assertEqual(summary["validation_metrics"]["roc_auc"], 0.9086)
        self.assertIn("distinction_note", summary)


if __name__ == "__main__":
    unittest.main()
