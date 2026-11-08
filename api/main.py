from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from api.schemas import HealthResponse
from api.services.model_service import ModelService, get_model_service
from api.routes import (
    predict_router,
    transactions_router,
    alerts_router,
    metrics_router,
    graph_router,
    monitoring_router
)

app = FastAPI(
    title="Real-Time Fraud Detection Platform API",
    description="High-throughput real-time financial fraud detection API using XGBoost and relationship analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local React and frontend dashboard integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(predict_router)
app.include_router(transactions_router)
app.include_router(alerts_router)
app.include_router(metrics_router)
app.include_router(graph_router)
app.include_router(monitoring_router)


@app.get("/", tags=["System"])
def root():
    """Root status endpoint."""
    return {
        "service": "Real-Time Fraud Detection Platform",
        "status": "operational",
        "version": "1.0.0",
        "documentation": "/docs",
        "model_status": "ready" if _service.model is not None else "unavailable"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(service: ModelService = Depends(get_model_service)) -> HealthResponse:
    """Service health and model availability check."""
    return service.get_health()


@app.get("/docs/pdf", tags=["Documentation"])
def download_documentation_pdf():
    """Download or view the comprehensive project documentation PDF."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_dir, "Real_Time_Fraud_Detection_Comprehensive_Documentation.pdf")
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="Real_Time_Fraud_Detection_Comprehensive_Documentation.pdf"
        )
    raise HTTPException(status_code=404, detail="Documentation PDF file not found.")


# Backwards-compatible exports
_service = get_model_service()
model = _service.model
threshold = _service.threshold
expected_features = _service.expected_features


def home():
    return root()


def health():
    return _service.get_health().model_dump()


def model_info():
    return _service.get_model_info().model_dump()


def predict(tx):
    return _service.predict(tx.transaction).model_dump()


def calculate_risk_level(prob, thresh):
    return _service.calculate_risk_level(prob)


from api.schemas import PredictionRequest as Transaction

