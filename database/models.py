from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON
)
from sqlalchemy.orm import relationship
from database.connection import Base


def utc_now():
    return datetime.now(timezone.utc)


class TransactionModel(Base):
    """Stores incoming financial transactions."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), unique=True, nullable=False, index=True)
    transaction_dt = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False, index=True)
    product_cd = Column(String(16), nullable=True)
    card1 = Column(Integer, nullable=True, index=True)  # Primary graph relationship proxy
    card2 = Column(Float, nullable=True)
    card3 = Column(Float, nullable=True)
    card4 = Column(String(32), nullable=True)
    card5 = Column(Float, nullable=True)
    card6 = Column(String(32), nullable=True)
    addr1 = Column(Float, nullable=True)
    addr2 = Column(Float, nullable=True)
    raw_features = Column(JSON, nullable=True)  # Complete 432-feature payload
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    prediction = relationship("PredictionModel", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    alert = relationship("AlertModel", back_populates="transaction", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transaction {self.transaction_id} amt=${self.amount}>"


class PredictionModel(Base):
    """Stores XGBoost inference results and assigned risk levels."""
    __tablename__ = "fraud_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    fraud_probability = Column(Float, nullable=False, index=True)
    prediction = Column(Integer, nullable=False, index=True)  # 0 = legitimate, 1 = fraud
    status = Column(String(32), nullable=False)  # "Fraud" | "Legitimate"
    risk_level = Column(String(16), nullable=False, index=True)  # "LOW", "MEDIUM", "HIGH"
    threshold = Column(Float, nullable=False)
    model_name = Column(String(128), default="XGBoost Fraud Classification Pipeline")
    model_version = Column(String(32), default="v1.0")
    inference_latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationship
    transaction = relationship("TransactionModel", back_populates="prediction")

    def __repr__(self):
        return f"<Prediction tx={self.transaction_id} prob={self.fraud_probability} risk={self.risk_level}>"


class AlertModel(Base):
    """Stores triggered fraud alerts requiring analyst review."""
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(64), unique=True, nullable=False, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    fraud_probability = Column(Float, nullable=False, index=True)
    risk_level = Column(String(16), nullable=False, index=True)
    alert_status = Column(String(32), default="TRIGGERED", nullable=False)  # "TRIGGERED", "WARNING", "RESOLVED"
    review_status = Column(String(32), default="PENDING", nullable=False, index=True)  # "PENDING", "INVESTIGATING", "CONFIRMED_FRAUD", "FALSE_POSITIVE", "DISMISSED"
    analyst_notes = Column(Text, nullable=True)
    suspicious_factors = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    transaction = relationship("TransactionModel", back_populates="alert")
    reviews = relationship("AnalystReviewModel", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Alert {self.alert_id} tx={self.transaction_id} status={self.review_status}>"


class AnalystReviewModel(Base):
    """Audit log of analyst decisions and triage notes."""
    __tablename__ = "analyst_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(64), ForeignKey("fraud_alerts.alert_id", ondelete="CASCADE"), nullable=False, index=True)
    review_status = Column(String(32), nullable=False, index=True)
    analyst_id = Column(String(64), default="security_analyst", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationship
    alert = relationship("AlertModel", back_populates="reviews")

    def __repr__(self):
        return f"<AnalystReview alert={self.alert_id} by={self.analyst_id} status={self.review_status}>"


class ModelMetadataModel(Base):
    """Persistent catalog of trained models and evaluation benchmarks."""
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(128), nullable=False)
    classifier = Column(String(64), nullable=False)
    version = Column(String(32), default="1.0.0", nullable=False)
    threshold = Column(Float, nullable=False)
    expected_feature_count = Column(Integer, nullable=False)
    roc_auc = Column(Float, nullable=True)
    pr_auc = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def __repr__(self):
        return f"<ModelMetadata name={self.model_name} ROC-AUC={self.roc_auc} PR-AUC={self.pr_auc}>"
