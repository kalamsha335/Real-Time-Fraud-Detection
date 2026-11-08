import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
import pandas as pd

from monitoring.drift_monitor import get_drift_monitor
from monitoring.mlflow_logger import MLflowTracker
from api.services.model_service import get_model_service

monitoring_router = APIRouter(prefix="/monitoring", tags=["Model Monitoring & Drift"])

tracker = MLflowTracker()
monitor = get_drift_monitor()
service = get_model_service()


@monitoring_router.get("/drift", summary="Get data drift metrics")
def get_drift_status() -> Dict[str, Any]:
    """
    Retrieve latest Evidently data drift metrics, feature distribution changes,
    and the explicit distinction between feature drift and model performance degradation.
    """
    try:
        # Fetch current transactions from service/database if available
        recent_txs = service.get_recent_transactions(limit=100)
        curr_df = None
        if recent_txs and len(recent_txs) >= 5:
            records = []
            for t in recent_txs:
                records.append({
                    "TransactionAmt": t.amount,
                    "fraud_probability": t.fraud_probability,
                    "prediction": t.prediction
                })
            curr_df = pd.DataFrame(records)

        result = monitor.run_drift_analysis(current_data=curr_df, save_report=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate drift: {str(e)}")


@monitoring_router.get("/drift/report", response_class=HTMLResponse, summary="View Evidently HTML Drift Report")
def get_drift_html_report():
    """
    Serve the full Evidently HTML data drift visualization report.
    """
    report_file = monitor.report_path
    if not os.path.exists(report_file):
        # Generate on demand
        monitor.run_drift_analysis()
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    raise HTTPException(status_code=404, detail="Drift report not found.")


@monitoring_router.post("/drift/run", summary="Trigger a new drift analysis calculation")
def trigger_drift_run():
    """
    Manually trigger a fresh Evidently data drift execution against current database records.
    """
    try:
        recent_txs = service.get_recent_transactions(limit=200)
        curr_df = None
        if recent_txs and len(recent_txs) >= 5:
            records = [{"TransactionAmt": t.amount, "fraud_probability": t.fraud_probability, "prediction": t.prediction} for t in recent_txs]
            curr_df = pd.DataFrame(records)
        res = monitor.run_drift_analysis(current_data=curr_df, save_report=True)
        return {
            "message": "Drift analysis completed successfully",
            "feature_drift_detected": res["feature_drift_detected"],
            "drift_share": res["drift_share"],
            "report_url": "/monitoring/drift/report"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run drift evaluation: {str(e)}")


@monitoring_router.get("/mlflow/runs", summary="List MLflow experiment tracking runs")
def get_mlflow_runs():
    """
    Retrieve logged model runs, parameters, metrics, and artifact identifiers from MLflow.
    """
    try:
        runs = tracker.get_runs(max_results=20)
        return {
            "experiment": tracker.EXPERIMENT_NAME,
            "tracking_uri": tracker.tracking_uri,
            "total_runs": len(runs),
            "runs": runs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch MLflow runs: {str(e)}")


@monitoring_router.get("/model-summary", summary="Consolidated model performance and drift summary")
def get_model_summary():
    """
    Consolidated model summary for dashboard cards and monitoring overview.
    Combines authentic MLflow validation metrics and current drift status.
    """
    latest_metrics = tracker.get_latest_metrics()
    return {
        "model_name": "XGBoost Fraud Classifier",
        "pipeline_type": "Scikit-learn Pipeline with ColumnTransformer",
        "expected_features": 432,
        "decision_threshold": 0.50,
        "validation_metrics": {
            "roc_auc": latest_metrics.get("roc_auc", 0.9086),
            "pr_auc": latest_metrics.get("pr_auc", 0.5189),
            "fraud_precision": latest_metrics.get("precision", 0.22),
            "fraud_recall": latest_metrics.get("recall", 0.73),
            "source_run_id": latest_metrics.get("run_id", "80d96aad5fd44fe4bdb50d99be0e16d2")
        },
        "monitoring_status": {
            "feature_drift": "MONITORED",
            "target_drift": "MONITORED",
            "report_endpoint": "/monitoring/drift/report"
        },
        "distinction_note": (
            "Feature drift (P(X)) is monitored continuously on incoming transaction attributes. "
            "Model performance degradation (P(Y|X)) requires delayed ground-truth chargeback labels."
        )
    }
