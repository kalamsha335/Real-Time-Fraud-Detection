from fastapi import APIRouter, Depends, Query, Path
from typing import Optional
from api.schemas import AlertsListResponse, AlertItem, AlertReviewUpdate
from api.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="/alerts", tags=["Fraud Alerts"])


@router.get(
    "",
    response_model=AlertsListResponse,
    summary="Get suspicious transaction alerts",
    description="Returns high-risk and flagged fraud transactions needing analyst investigation."
)
def list_alerts(
    limit: int = Query(50, ge=1, le=500, description="Max number of alerts to retrieve"),
    review_status: Optional[str] = Query(None, description="Filter by review status: PENDING, INVESTIGATING, CONFIRMED_FRAUD, FALSE_POSITIVE"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: HIGH, MEDIUM"),
    service: ModelService = Depends(get_model_service)
) -> AlertsListResponse:
    alerts = service.get_alerts(
        limit=limit,
        review_status=review_status,
        risk_level=risk_level
    )
    pending_count = len([a for a in alerts if a.review_status == "PENDING"])
    return AlertsListResponse(
        total=len(alerts),
        pending_count=pending_count,
        alerts=alerts
    )


@router.patch(
    "/{alert_id}/review",
    response_model=AlertItem,
    summary="Update analyst review status on an alert",
    description="Updates the analyst review disposition (e.g. CONFIRMED_FRAUD, FALSE_POSITIVE) with notes."
)
def update_alert_status(
    alert_id: str = Path(..., description="Alert ID to update"),
    update_data: AlertReviewUpdate = ...,
    service: ModelService = Depends(get_model_service)
) -> AlertItem:
    return service.update_alert_review(
        alert_id=alert_id,
        review_status=update_data.review_status.value,
        notes=update_data.analyst_notes,
        reviewed_by=update_data.reviewed_by
    )

