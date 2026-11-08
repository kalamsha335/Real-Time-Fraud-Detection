from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DISMISSED = "DISMISSED"


class PredictionRequest(BaseModel):
    transaction: Dict[str, Any] = Field(
        ...,
        description="Key-value mapping of all 432 transaction features as expected by the trained pipeline"
    )
    transaction_id: Optional[str] = Field(
        None,
        description="Optional custom transaction identifier"
    )
    timestamp: Optional[str] = Field(
        None,
        description="Optional ISO 8601 transaction timestamp"
    )


class PredictionResponse(BaseModel):
    transaction_id: str
    fraud_probability: float
    prediction: int
    status: str
    risk_level: str
    threshold: float
    timestamp: str
    inference_latency_ms: float


class TransactionItem(BaseModel):
    transaction_id: str
    amount: float
    card1: Optional[int] = None
    product_cd: Optional[str] = None
    fraud_probability: float
    prediction: int
    risk_level: str
    status: str
    timestamp: str
    features_preview: Optional[Dict[str, Any]] = None


class TransactionsListResponse(BaseModel):
    total: int
    limit: int
    transactions: List[TransactionItem]


class AlertItem(BaseModel):
    alert_id: str
    transaction_id: str
    amount: float
    fraud_probability: float
    risk_level: str
    alert_status: str
    review_status: str
    analyst_notes: Optional[str] = None
    timestamp: str
    suspicious_factors: Optional[List[str]] = None


class AlertsListResponse(BaseModel):
    total: int
    pending_count: int
    alerts: List[AlertItem]


class AlertReviewUpdate(BaseModel):
    review_status: ReviewStatus
    analyst_notes: Optional[str] = Field(
        None,
        description="Optional analyst rationale or resolution notes"
    )
    reviewed_by: Optional[str] = Field(
        "security_analyst",
        description="Analyst identity or username"
    )


class SystemMetricsResponse(BaseModel):
    total_transactions: int
    fraudulent_detected: int
    legitimate_transactions: int
    fraud_detection_rate: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_fraud_probability: float
    average_latency_ms: float
    model_name: str
    threshold: float
    uptime_seconds: float


class ModelInfoResponse(BaseModel):
    model_name: str
    classifier: str
    threshold: float
    expected_feature_count: int
    features: List[str]


class HealthResponse(BaseModel):
    status: str
    model: str
    model_loaded: bool
    threshold: float
    features_expected: int
    database_connected: bool
    active_alerts_count: int


class SimulationRequest(BaseModel):
    scenario: str = Field(
        "random",
        description="Transaction simulation profile: 'random', 'legitimate', 'suspicious', 'fraud'"
    )
    count: int = Field(
        1,
        ge=1,
        le=50,
        description="Number of transactions to generate and evaluate"
    )


class SimulationResponse(BaseModel):
    delivered: int
    scenario: str
    results: List[PredictionResponse]

