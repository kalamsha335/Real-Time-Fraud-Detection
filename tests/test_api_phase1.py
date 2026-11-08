import unittest
import json
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.main import (
    app,
    model,
    threshold,
    expected_features,
    home,
    health,
    model_info,
    predict,
    Transaction,
    calculate_risk_level
)
from fastapi import HTTPException


class TestPhase1ModelLoadingAndAPI(unittest.TestCase):

    def test_01_model_loading(self):
        """Verify model, threshold, and feature expectations load properly."""
        self.assertIsNotNone(model, "Model failed to load.")
        self.assertIsInstance(threshold, float, "Threshold is not a float.")
        self.assertEqual(len(expected_features), 432, f"Expected 432 features, got {len(expected_features)}")
        self.assertEqual(threshold, 0.5, f"Expected threshold 0.5, got {threshold}")

    def test_02_home_endpoint(self):
        """Verify root endpoint response."""
        res = home()
        self.assertEqual(res["version"], "1.0.0")
        self.assertEqual(res["model_status"], "ready")

    def test_03_health_endpoint(self):
        """Verify health check endpoint returns model health status."""
        res = health()
        self.assertEqual(res["status"], "healthy")
        self.assertEqual(res["model"], "XGBoost")
        self.assertTrue(res["model_loaded"])
        self.assertEqual(res["features_expected"], 432)

    def test_04_model_info_endpoint(self):
        """Verify model info metadata endpoint."""
        res = model_info()
        self.assertEqual(res["classifier"], "XGBClassifier")
        self.assertEqual(res["expected_feature_count"], 432)
        self.assertEqual(len(res["features"]), 432)

    def test_05_predict_missing_features(self):
        """Verify predicting with missing features raises 400 error."""
        incomplete_payload = Transaction(transaction={"TransactionAmt": 150.0, "ProductCD": "W"})
        with self.assertRaises(HTTPException) as ctx:
            predict(incomplete_payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("missing_features", ctx.exception.detail)
        self.assertEqual(ctx.exception.detail["missing_count"], 430)

    def test_06_predict_full_transaction(self):
        """Verify end-to-end prediction with actual 432 features."""
        sample_path = os.path.join(os.path.dirname(__file__), "sample_transaction.json")
        self.assertTrue(os.path.exists(sample_path), "sample_transaction.json is missing")
        with open(sample_path, "r") as f:
            sample_data = json.load(f)

        tx = Transaction(transaction=sample_data)
        res = predict(tx)

        self.assertIn("fraud_probability", res)
        self.assertIn("prediction", res)
        self.assertIn("status", res)
        self.assertIn("risk_level", res)
        self.assertIn("threshold", res)

        self.assertGreaterEqual(res["fraud_probability"], 0.0)
        self.assertLessEqual(res["fraud_probability"], 1.0)
        self.assertIn(res["prediction"], [0, 1])
        self.assertIn(res["risk_level"], ["LOW", "MEDIUM", "HIGH"])
        self.assertEqual(res["status"], "Fraud" if res["prediction"] == 1 else "Legitimate")

    def test_07_risk_level_boundaries(self):
        """Test risk level classification logic."""
        self.assertEqual(calculate_risk_level(0.05, 0.5), "LOW")
        self.assertEqual(calculate_risk_level(0.20, 0.5), "MEDIUM")
        self.assertEqual(calculate_risk_level(0.49, 0.5), "MEDIUM")
        self.assertEqual(calculate_risk_level(0.50, 0.5), "HIGH")
        self.assertEqual(calculate_risk_level(0.85, 0.5), "HIGH")


if __name__ == "__main__":
    unittest.main()

