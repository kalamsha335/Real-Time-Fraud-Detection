from fastapi import APIRouter, Depends
from api.schemas import SystemMetricsResponse
from api.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="/metrics", tags=["System Metrics"])


@router.get(
    "",
    response_model=SystemMetricsResponse,
    summary="Get fraud detection performance and system statistics",
    description="Returns aggregate counts, fraud detection rate, risk distributions, and latency metrics."
)
def get_system_metrics(
    service: ModelService = Depends(get_model_service)
) -> SystemMetricsResponse:
    return service.get_metrics()

