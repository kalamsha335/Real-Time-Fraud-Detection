import unittest
import json
import os
import sys
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.connection import engine, SessionLocal, check_db_connection
from database.init_db import init_db
from database.models import (
    TransactionModel,
    PredictionModel,
    AlertModel,
    AnalystReviewModel,
    ModelMetadataModel
)
from database.repository import DatabaseRepository
from api.services.model_service import ModelService
from api.schemas import PredictionResponse, AlertItem


class TestPhase3DatabaseStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        sample_path = os.path.join(os.path.dirname(__file__), "sample_transaction.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            cls.sample_data = json.load(f)
        cls.service = ModelService.get_instance()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_01_db_connection_health(self):
        """Verify database connectivity."""
        is_conn, status, dialect = check_db_connection()
        self.assertTrue(is_conn)
        self.assertEqual(status, "connected")
        self.assertTrue(len(dialect) > 0)

    def test_02_model_metadata_seeded(self):
        """Verify model benchmark metadata is stored."""
        meta = self.db.query(ModelMetadataModel).filter(
            ModelMetadataModel.model_name == "XGBoost Fraud Classification Pipeline"
        ).first()
        self.assertIsNotNone(meta)
        self.assertEqual(meta.threshold, 0.5)
        self.assertEqual(meta.expected_feature_count, 432)
        self.assertAlmostEqual(meta.roc_auc, 0.9086, places=3)
        self.assertAlmostEqual(meta.pr_auc, 0.5189, places=3)

    def test_03_transaction_persistence(self):
        """Test persisting a transaction record."""
        tx_id = f"TX-DB-UNIT-{uuid.uuid4().hex[:8]}"
        tx = DatabaseRepository.save_transaction(self.db, tx_id, self.sample_data)
        self.assertIsNotNone(tx.id)
        self.assertEqual(tx.transaction_id, tx_id)
        self.assertEqual(tx.amount, float(self.sample_data.get("TransactionAmt", 0.0)))
        self.assertEqual(tx.card1, int(self.sample_data.get("card1")))

    def test_04_prediction_persistence(self):
        """Test persisting prediction linked to transaction."""
        tx_id = f"TX-DB-UNIT-{uuid.uuid4().hex[:8]}"
        DatabaseRepository.save_transaction(self.db, tx_id, self.sample_data)
        pred = PredictionResponse(
            transaction_id=tx_id,
            fraud_probability=0.75,
            prediction=1,
            status="Fraud",
            risk_level="HIGH",
            threshold=0.5,
            timestamp="2026-11-05T12:00:00Z",
            inference_latency_ms=12.5
        )
        saved = DatabaseRepository.save_prediction(self.db, pred)
        self.assertIsNotNone(saved.id)
        self.assertEqual(saved.transaction_id, tx_id)
        self.assertEqual(saved.prediction, 1)
        self.assertEqual(saved.risk_level, "HIGH")

    def test_05_alert_creation_and_review_audit_log(self):
        """Test alert creation and subsequent analyst review audit trail."""
        tx_id = f"TX-DB-UNIT-{uuid.uuid4().hex[:8]}"
        alt_id = f"ALT-UNIT-{uuid.uuid4().hex[:8]}"
        DatabaseRepository.save_transaction(self.db, tx_id, self.sample_data)
        alert_item = AlertItem(
            alert_id=alt_id,
            transaction_id=tx_id,
            amount=68.5,
            fraud_probability=0.75,
            risk_level="HIGH",
            alert_status="TRIGGERED",
            review_status="PENDING",
            analyst_notes=None,
            timestamp="2026-11-05T12:00:00Z",
            suspicious_factors=["High probability"]
        )
        saved_alert = DatabaseRepository.create_alert(self.db, alert_item)
        self.assertEqual(saved_alert.alert_id, alt_id)

        # Update analyst review
        updated = DatabaseRepository.update_alert_review(
            db=self.db,
            alert_id=alt_id,
            review_status="CONFIRMED_FRAUD",
            notes="Confirmed malicious card behavior",
            analyst_id="lead_investigator_1"
        )
        self.assertEqual(updated.review_status, "CONFIRMED_FRAUD")
        self.assertEqual(updated.alert_status, "RESOLVED")

        # Verify audit review entry exists in analyst_reviews table
        review_entry = self.db.query(AnalystReviewModel).filter(
            AnalystReviewModel.alert_id == alt_id
        ).first()
        self.assertIsNotNone(review_entry)
        self.assertEqual(review_entry.analyst_id, "lead_investigator_1")
        self.assertEqual(review_entry.review_status, "CONFIRMED_FRAUD")

    def test_06_end_to_end_model_service_persistence(self):
        """Test that calling service.predict() automatically writes to database."""
        tx_id = f"TX-SERVICE-E2E-{uuid.uuid4().hex[:8]}"
        res = self.service.predict(self.sample_data, transaction_id=tx_id)
        self.assertEqual(res.transaction_id, tx_id)

        # Verify in database
        saved_tx = self.db.query(TransactionModel).filter(TransactionModel.transaction_id == tx_id).first()
        self.assertIsNotNone(saved_tx)

        saved_pred = self.db.query(PredictionModel).filter(PredictionModel.transaction_id == tx_id).first()
        self.assertIsNotNone(saved_pred)
        self.assertEqual(saved_pred.fraud_probability, res.fraud_probability)

        # Verify query method retrieves this transaction
        recent = DatabaseRepository.get_recent_transactions(self.db, limit=10)
        self.assertTrue(any(t.transaction_id == tx_id for t in recent))

    def test_07_database_metrics_aggregation(self):
        """Test system metrics calculated from database rows."""
        metrics = DatabaseRepository.get_system_metrics(self.db, uptime_seconds=100.0)
        self.assertGreaterEqual(metrics.total_transactions, 1)
        self.assertGreaterEqual(metrics.fraudulent_detected, 1)
        self.assertGreater(metrics.fraud_detection_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
