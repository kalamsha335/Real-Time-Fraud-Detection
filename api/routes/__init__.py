"""API Routes module."""
from .predict import router as predict_router
from .transactions import router as transactions_router
from .alerts import router as alerts_router
from .metrics import router as metrics_router
from .graph_routes import router as graph_router
from .monitoring_routes import monitoring_router

__all__ = [
    "predict_router",
    "transactions_router",
    "alerts_router",
    "metrics_router",
    "graph_router",
    "monitoring_router"
]

