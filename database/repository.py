import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database.models import (
    TransactionModel,
    PredictionModel,
    AlertModel,
    AnalystReviewModel,
    ModelMetadataModel
)
from api.schemas import PredictionResponse, TransactionItem, AlertItem, SystemMetricsResponse

logger = logging.getLogger("db_repository")


class DatabaseRepository:

    @staticmethod
    def save_transaction(
        db: Session,
        tx_id: str,
        transaction_data: Dict[str, Any]
    ) -> TransactionModel:
        """Persist transaction record with relationship anchors (idempotent)."""
        existing = db.query(TransactionModel).filter(TransactionModel.transaction_id == tx_id).first()
        if existing:
            return existing

        tx = TransactionModel(
            transaction_id=tx_id,
            transaction_dt=int(transaction_data.get("TransactionDT")) if transaction_data.get("TransactionDT") is not None else None,
            amount=float(transaction_data.get("TransactionAmt", 0.0)),
            product_cd=str(transaction_data.get("ProductCD")) if transaction_data.get("ProductCD") else None,
            card1=int(transaction_data.get("card1")) if transaction_data.get("card1") is not None else None,
            card2=float(transaction_data.get("card2")) if transaction_data.get("card2") is not None else None,
            card3=float(transaction_data.get("card3")) if transaction_data.get("card3") is not None else None,
            card4=str(transaction_data.get("card4")) if transaction_data.get("card4") else None,
            card5=float(transaction_data.get("card5")) if transaction_data.get("card5") is not None else None,
            card6=str(transaction_data.get("card6")) if transaction_data.get("card6") else None,
            addr1=float(transaction_data.get("addr1")) if transaction_data.get("addr1") is not None else None,
            addr2=float(transaction_data.get("addr2")) if transaction_data.get("addr2") is not None else None,
            raw_features=transaction_data
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def save_prediction(
        db: Session,
        prediction: PredictionResponse
    ) -> PredictionModel:
        """Persist prediction result (idempotent)."""
        existing = db.query(PredictionModel).filter(PredictionModel.transaction_id == prediction.transaction_id).first()
        if existing:
            return existing

        pred = PredictionModel(
            transaction_id=prediction.transaction_id,
            fraud_probability=prediction.fraud_probability,
            prediction=prediction.prediction,
            status=prediction.status,
            risk_level=prediction.risk_level,
            threshold=prediction.threshold,
            inference_latency_ms=prediction.inference_latency_ms
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)
        return pred

    @staticmethod
    def create_alert(
        db: Session,
        alert_item: AlertItem
    ) -> AlertModel:
        """Persist high-risk alert (idempotent)."""
        existing = db.query(AlertModel).filter(
            (AlertModel.alert_id == alert_item.alert_id) |
            (AlertModel.transaction_id == alert_item.transaction_id)
        ).first()
        if existing:
            return existing

        alt = AlertModel(
            alert_id=alert_item.alert_id,
            transaction_id=alert_item.transaction_id,
            amount=alert_item.amount,
            fraud_probability=alert_item.fraud_probability,
            risk_level=alert_item.risk_level,
            alert_status=alert_item.alert_status,
            review_status=alert_item.review_status,
            analyst_notes=alert_item.analyst_notes,
            suspicious_factors=alert_item.suspicious_factors
        )
        db.add(alt)
        db.commit()
        db.refresh(alt)
        return alt

    @staticmethod
    def update_alert_review(
        db: Session,
        alert_id: str,
        review_status: str,
        notes: Optional[str] = None,
        analyst_id: str = "security_analyst"
    ) -> Optional[AlertModel]:
        """Update alert triage status and record review audit trail."""
        alert = db.query(AlertModel).filter(AlertModel.alert_id == alert_id).first()
        if not alert:
            return None

        alert.review_status = review_status
        if review_status in ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "DISMISSED"]:
            alert.alert_status = "RESOLVED"

        if notes:
            alert.analyst_notes = f"[{analyst_id}] {notes}" if not alert.analyst_notes else f"{alert.analyst_notes}\n[{analyst_id}] {notes}"

        # Record review event
        review_log = AnalystReviewModel(
            alert_id=alert_id,
            review_status=review_status,
            analyst_id=analyst_id,
            notes=notes
        )
        db.add(review_log)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_recent_transactions(
        db: Session,
        limit: int = 50,
        risk_level: Optional[str] = None,
        prediction: Optional[int] = None
    ) -> List[TransactionItem]:
        """Retrieve recent transactions joined with predictions."""
        query = (
            db.query(TransactionModel, PredictionModel)
            .join(PredictionModel, TransactionModel.transaction_id == PredictionModel.transaction_id)
            .order_by(desc(TransactionModel.created_at))
        )

        if risk_level:
            query = query.filter(PredictionModel.risk_level == risk_level.upper())
        if prediction is not None:
            query = query.filter(PredictionModel.prediction == prediction)

        records = query.limit(limit).all()
        result = []
        for tx, pred in records:
            result.append(
                TransactionItem(
                    transaction_id=tx.transaction_id,
                    amount=tx.amount,
                    card1=tx.card1,
                    product_cd=tx.product_cd,
                    fraud_probability=pred.fraud_probability,
                    prediction=pred.prediction,
                    risk_level=pred.risk_level,
                    status=pred.status,
                    timestamp=tx.created_at.isoformat(),
                    features_preview={
                        "TransactionAmt": tx.amount,
                        "card1": tx.card1,
                        "ProductCD": tx.product_cd,
                        "card4": tx.card4,
                        "card6": tx.card6
                    }
                )
            )
        return result

    @staticmethod
    def get_alerts(
        db: Session,
        limit: int = 50,
        review_status: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> List[AlertItem]:
        """Retrieve alerts ordered by creation time."""
        query = db.query(AlertModel).order_by(desc(AlertModel.created_at))
        if review_status:
            query = query.filter(AlertModel.review_status == review_status.upper())
        if risk_level:
            query = query.filter(AlertModel.risk_level == risk_level.upper())

        alerts = query.limit(limit).all()
        return [
            AlertItem(
                alert_id=a.alert_id,
                transaction_id=a.transaction_id,
                amount=a.amount,
                fraud_probability=a.fraud_probability,
                risk_level=a.risk_level,
                alert_status=a.alert_status,
                review_status=a.review_status,
                analyst_notes=a.analyst_notes,
                timestamp=a.created_at.isoformat(),
                suspicious_factors=a.suspicious_factors
            )
            for a in alerts
        ]

    @staticmethod
    def get_system_metrics(db: Session, uptime_seconds: float) -> SystemMetricsResponse:
        """Compute aggregate platform performance metrics from database."""
        total = db.query(func.count(PredictionModel.id)).scalar() or 0
        fraud_count = db.query(func.count(PredictionModel.id)).filter(PredictionModel.prediction == 1).scalar() or 0
        legit_count = total - fraud_count

        high_count = db.query(func.count(PredictionModel.id)).filter(PredictionModel.risk_level == "HIGH").scalar() or 0
        med_count = db.query(func.count(PredictionModel.id)).filter(PredictionModel.risk_level == "MEDIUM").scalar() or 0
        low_count = db.query(func.count(PredictionModel.id)).filter(PredictionModel.risk_level == "LOW").scalar() or 0

        avg_prob = db.query(func.avg(PredictionModel.fraud_probability)).scalar() or 0.0
        avg_latency = db.query(func.avg(PredictionModel.inference_latency_ms)).scalar() or 0.0

        rate = round((fraud_count / total * 100), 2) if total > 0 else 0.0

        return SystemMetricsResponse(
            total_transactions=total,
            fraudulent_detected=fraud_count,
            legitimate_transactions=legit_count,
            fraud_detection_rate=rate,
            high_risk_count=high_count,
            medium_risk_count=med_count,
            low_risk_count=low_count,
            average_fraud_probability=round(float(avg_prob), 4),
            average_latency_ms=round(float(avg_latency), 2),
            model_name="XGBoost Fraud Classification Pipeline",
            threshold=0.5,
            uptime_seconds=round(uptime_seconds, 1)
        )

    @staticmethod
    def seed_model_metadata(
        db: Session,
        model_name: str,
        classifier: str,
        threshold: float,
        features_count: int,
        roc_auc: float = 0.9086,
        pr_auc: float = 0.5189,
        precision: float = 0.22,
        recall: float = 0.73
    ) -> ModelMetadataModel:
        """Seed initial model benchmark record if not present."""
        existing = db.query(ModelMetadataModel).filter(ModelMetadataModel.model_name == model_name).first()
        if existing:
            return existing

        meta = ModelMetadataModel(
            model_name=model_name,
            classifier=classifier,
            version="1.0.0",
            threshold=threshold,
            expected_feature_count=features_count,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            precision=precision,
            recall=recall,
            is_active=True
        )
        db.add(meta)
        db.commit()
        db.refresh(meta)
        return meta
