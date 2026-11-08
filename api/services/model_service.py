import os
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import deque
import threading

import joblib
import pandas as pd
from fastapi import HTTPException, status

from api.schemas import (
    PredictionResponse,
    TransactionItem,
    AlertItem,
    SystemMetricsResponse,
    ModelInfoResponse,
    HealthResponse,
    RiskLevel,
    ReviewStatus
)
from database.connection import SessionLocal, check_db_connection
from database.repository import DatabaseRepository

logger = logging.getLogger("model_service")
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resolve_file_path(filename: str, env_var: Optional[str] = None) -> str:
    """Resolve file path across environment variable, models/, notebooks/, and root."""
    if env_var and os.getenv(env_var):
        env_val = os.getenv(env_var)
        if os.path.isabs(env_val) and os.path.exists(env_val):
            return env_val
        relative_path = os.path.join(BASE_DIR, env_val)
        if os.path.exists(relative_path):
            return relative_path

    search_dirs = [
        os.path.join(BASE_DIR, "models", filename),
        os.path.join(BASE_DIR, "notebooks", filename),
        os.path.join(BASE_DIR, filename),
    ]

    for path in search_dirs:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        f"Unable to find '{filename}'. Searched paths: {search_dirs}"
    )


class ModelService:
    _instance: Optional["ModelService"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.start_time = time.time()
        self.model = None
        self.threshold = 0.5
        self.expected_features: List[str] = []
        self.load_model()

        # Thread-safe in-memory cache
        self.transactions_buffer = deque(maxlen=2000)
        self.alerts_dict: Dict[str, AlertItem] = {}
        self.data_lock = threading.Lock()

        # In-memory metrics fallback counters
        self.total_transactions_count = 0
        self.fraudulent_count = 0
        self.legitimate_count = 0
        self.high_risk_count = 0
        self.medium_risk_count = 0
        self.low_risk_count = 0
        self.total_probability_sum = 0.0
        self.total_latency_ms = 0.0

    @classmethod
    def get_instance(cls) -> "ModelService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load_model(self) -> None:
        """Load the trained XGBoost Pipeline model and decision threshold."""
        try:
            model_path = resolve_file_path("fraud_detection_xgboost.pkl", "MODEL_PATH")
            self.model = joblib.load(model_path)
            logger.info("Successfully loaded XGBoost pipeline from %s", model_path)
        except Exception as e:
            logger.error("Error loading model: %s", e)
            self.model = None

        try:
            threshold_path = resolve_file_path("fraud_threshold.pkl", "THRESHOLD_PATH")
            self.threshold = float(joblib.load(threshold_path))
            logger.info("Successfully loaded threshold (%.4f) from %s", self.threshold, threshold_path)
        except Exception as e:
            logger.warning("Failed to load threshold, using default 0.5: %s", e)
            self.threshold = 0.5

        if self.model is not None and hasattr(self.model, "named_steps"):
            preprocessor = self.model.named_steps.get("preprocessor")
            if preprocessor and hasattr(preprocessor, "feature_names_in_"):
                self.expected_features = list(preprocessor.feature_names_in_)
                logger.info("Pipeline expects %d input features", len(self.expected_features))

    def calculate_risk_level(self, probability: float) -> str:
        if probability >= self.threshold:
            return RiskLevel.HIGH.value
        elif probability >= 0.20:
            return RiskLevel.MEDIUM.value
        return RiskLevel.LOW.value

    def predict(
        self,
        transaction_data: Dict[str, Any],
        transaction_id: Optional[str] = None,
        custom_timestamp: Optional[str] = None
    ) -> PredictionResponse:
        """
        Validate input, execute inference using the exact 432-feature schema,
        and persist transaction, prediction & alert state into PostgreSQL.
        """
        if self.model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model is unavailable or not loaded"
            )

        start_ts = time.time()
        tx_id = transaction_id or f"TX-{uuid.uuid4().hex[:10].upper()}"
        iso_timestamp = custom_timestamp or datetime.now(timezone.utc).isoformat()

        # Validate required features
        input_keys = set(transaction_data.keys())
        missing_features = [f for f in self.expected_features if f not in input_keys]

        if missing_features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Missing required transaction features",
                    "missing_count": len(missing_features),
                    "missing_features": missing_features[:20] if len(missing_features) > 20 else missing_features
                }
            )

        # Build DataFrame maintaining exact feature ordering expected by pipeline
        input_df = pd.DataFrame([transaction_data])[self.expected_features]

        try:
            # Predict probability via pipeline without secondary preprocessing
            raw_prob = float(self.model.predict_proba(input_df)[0][1])
            fraud_prob = round(raw_prob, 4)
            prediction = int(fraud_prob >= self.threshold)
            risk_level = self.calculate_risk_level(fraud_prob)
            status_label = "Fraud" if prediction == 1 else "Legitimate"

            latency_ms = round((time.time() - start_ts) * 1000, 2)

            amt = float(transaction_data.get("TransactionAmt") or 0.0)
            card1 = int(transaction_data.get("card1")) if transaction_data.get("card1") is not None else None
            product_cd = str(transaction_data.get("ProductCD")) if transaction_data.get("ProductCD") else None

            tx_item = TransactionItem(
                transaction_id=tx_id,
                amount=amt,
                card1=card1,
                product_cd=product_cd,
                fraud_probability=fraud_prob,
                prediction=prediction,
                risk_level=risk_level,
                status=status_label,
                timestamp=iso_timestamp,
                features_preview={
                    "TransactionAmt": amt,
                    "ProductCD": product_cd,
                    "card1": card1,
                    "card4": transaction_data.get("card4"),
                    "card6": transaction_data.get("card6")
                }
            )

            alert_item: Optional[AlertItem] = None
            if prediction == 1 or risk_level in [RiskLevel.HIGH.value, RiskLevel.MEDIUM.value]:
                alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
                factors = [f"Fraud Probability: {fraud_prob:.4f} (Threshold: {self.threshold})"]
                if amt > 500:
                    factors.append(f"High Transaction Amount: ${amt:.2f}")
                if card1:
                    factors.append(f"Card Relationship Anchor: card1={card1}")

                alert_item = AlertItem(
                    alert_id=alert_id,
                    transaction_id=tx_id,
                    amount=amt,
                    fraud_probability=fraud_prob,
                    risk_level=risk_level,
                    alert_status="TRIGGERED" if prediction == 1 else "WARNING",
                    review_status=ReviewStatus.PENDING.value,
                    analyst_notes=None,
                    timestamp=iso_timestamp,
                    suspicious_factors=factors
                )

            # Update in-memory state
            with self.data_lock:
                self.transactions_buffer.appendleft(tx_item)
                self.total_transactions_count += 1
                self.total_probability_sum += fraud_prob
                self.total_latency_ms += latency_ms

                if prediction == 1:
                    self.fraudulent_count += 1
                else:
                    self.legitimate_count += 1

                if risk_level == RiskLevel.HIGH.value:
                    self.high_risk_count += 1
                elif risk_level == RiskLevel.MEDIUM.value:
                    self.medium_risk_count += 1
                else:
                    self.low_risk_count += 1

                if alert_item:
                    self.alerts_dict[alert_item.alert_id] = alert_item

            pred_response = PredictionResponse(
                transaction_id=tx_id,
                fraud_probability=fraud_prob,
                prediction=prediction,
                status=status_label,
                risk_level=risk_level,
                threshold=self.threshold,
                timestamp=iso_timestamp,
                inference_latency_ms=latency_ms
            )

            # Persist to database
            try:
                db = SessionLocal()
                try:
                    DatabaseRepository.save_transaction(db, tx_id, transaction_data)
                    DatabaseRepository.save_prediction(db, pred_response)
                    if alert_item:
                        DatabaseRepository.create_alert(db, alert_item)
                finally:
                    db.close()
            except Exception as dbe:
                logger.warning("Database persistence error for tx %s: %s", tx_id, dbe)

            return pred_response

        except Exception as e:
            logger.exception("Inference processing error for tx %s: %s", tx_id, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference error: {str(e)}"
            )

    def get_recent_transactions(
        self,
        limit: int = 50,
        risk_level: Optional[str] = None,
        prediction: Optional[int] = None
    ) -> List[TransactionItem]:
        # Try database first
        try:
            db = SessionLocal()
            try:
                db_results = DatabaseRepository.get_recent_transactions(
                    db=db, limit=limit, risk_level=risk_level, prediction=prediction
                )
                if db_results:
                    return db_results
            finally:
                db.close()
        except Exception as dbe:
            logger.debug("Database query fallback to in-memory: %s", dbe)

        with self.data_lock:
            results = list(self.transactions_buffer)

        if risk_level:
            results = [tx for tx in results if tx.risk_level.upper() == risk_level.upper()]
        if prediction is not None:
            results = [tx for tx in results if tx.prediction == prediction]

        return results[:limit]

    def get_alerts(
        self,
        limit: int = 50,
        review_status: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> List[AlertItem]:
        # Try database first
        try:
            db = SessionLocal()
            try:
                db_alerts = DatabaseRepository.get_alerts(
                    db=db, limit=limit, review_status=review_status, risk_level=risk_level
                )
                if db_alerts:
                    return db_alerts
            finally:
                db.close()
        except Exception as dbe:
            logger.debug("Database query fallback to in-memory: %s", dbe)

        with self.data_lock:
            alerts = list(self.alerts_dict.values())

        if review_status:
            alerts = [a for a in alerts if a.review_status.upper() == review_status.upper()]
        if risk_level:
            alerts = [a for a in alerts if a.risk_level.upper() == risk_level.upper()]

        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]

    def update_alert_review(
        self,
        alert_id: str,
        review_status: str,
        notes: Optional[str] = None,
        reviewed_by: Optional[str] = None
    ) -> AlertItem:
        # Update in database
        db_alert = None
        try:
            db = SessionLocal()
            try:
                db_alert = DatabaseRepository.update_alert_review(
                    db=db,
                    alert_id=alert_id,
                    review_status=review_status,
                    notes=notes,
                    analyst_id=reviewed_by or "security_analyst"
                )
            finally:
                db.close()
        except Exception as dbe:
            logger.warning("Database error on alert review: %s", dbe)

        # Update in-memory cache
        with self.data_lock:
            if alert_id in self.alerts_dict:
                alert = self.alerts_dict[alert_id]
                updated_notes = notes or alert.analyst_notes
                if reviewed_by:
                    updated_notes = f"[{reviewed_by}] {updated_notes}" if updated_notes else f"Reviewed by {reviewed_by}"

                updated_alert = AlertItem(
                    alert_id=alert.alert_id,
                    transaction_id=alert.transaction_id,
                    amount=alert.amount,
                    fraud_probability=alert.fraud_probability,
                    risk_level=alert.risk_level,
                    alert_status="RESOLVED" if review_status in ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "DISMISSED"] else alert.alert_status,
                    review_status=review_status,
                    analyst_notes=updated_notes,
                    timestamp=alert.timestamp,
                    suspicious_factors=alert.suspicious_factors
                )
                self.alerts_dict[alert_id] = updated_alert
                return updated_alert

        if db_alert:
            return AlertItem(
                alert_id=db_alert.alert_id,
                transaction_id=db_alert.transaction_id,
                amount=db_alert.amount,
                fraud_probability=db_alert.fraud_probability,
                risk_level=db_alert.risk_level,
                alert_status=db_alert.alert_status,
                review_status=db_alert.review_status,
                analyst_notes=db_alert.analyst_notes,
                timestamp=db_alert.created_at.isoformat(),
                suspicious_factors=db_alert.suspicious_factors
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found"
        )

    def get_metrics(self) -> SystemMetricsResponse:
        uptime = round(time.time() - self.start_time, 1)

        # Try database first
        try:
            db = SessionLocal()
            try:
                db_metrics = DatabaseRepository.get_system_metrics(db, uptime)
                if db_metrics.total_transactions > 0:
                    return db_metrics
            finally:
                db.close()
        except Exception as dbe:
            logger.debug("Database metrics fallback to in-memory: %s", dbe)

        with self.data_lock:
            total = self.total_transactions_count
            fraud_count = self.fraudulent_count
            legit_count = self.legitimate_count
            high_count = self.high_risk_count
            med_count = self.medium_risk_count
            low_count = self.low_risk_count
            avg_prob = (self.total_probability_sum / total) if total > 0 else 0.0
            avg_latency = (self.total_latency_ms / total) if total > 0 else 0.0

        detection_rate = round((fraud_count / total * 100), 2) if total > 0 else 0.0

        return SystemMetricsResponse(
            total_transactions=total,
            fraudulent_detected=fraud_count,
            legitimate_transactions=legit_count,
            fraud_detection_rate=detection_rate,
            high_risk_count=high_count,
            medium_risk_count=med_count,
            low_risk_count=low_count,
            average_fraud_probability=round(avg_prob, 4),
            average_latency_ms=round(avg_latency, 2),
            model_name="XGBoost Fraud Classification Pipeline",
            threshold=self.threshold,
            uptime_seconds=uptime
        )

    def get_model_info(self) -> ModelInfoResponse:
        classifier_name = "XGBClassifier"
        if self.model and hasattr(self.model, "named_steps") and "classifier" in self.model.named_steps:
            classifier_name = type(self.model.named_steps["classifier"]).__name__

        return ModelInfoResponse(
            model_name="XGBoost Fraud Classification Pipeline",
            classifier=classifier_name,
            threshold=self.threshold,
            expected_feature_count=len(self.expected_features),
            features=self.expected_features
        )

    def get_health(self) -> HealthResponse:
        is_conn, status_msg, dialect = check_db_connection()
        with self.data_lock:
            active_alerts = len([a for a in self.alerts_dict.values() if a.review_status == ReviewStatus.PENDING.value])

        return HealthResponse(
            status="healthy" if self.model is not None and is_conn else "degraded",
            model="XGBoost" if self.model is not None else "None",
            model_loaded=self.model is not None,
            threshold=self.threshold,
            features_expected=len(self.expected_features),
            database_connected=is_conn,
            active_alerts_count=active_alerts
        )


def get_model_service() -> ModelService:
    return ModelService.get_instance()
