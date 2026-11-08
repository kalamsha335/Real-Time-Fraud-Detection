from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, List
from api.schemas import TransactionsListResponse, TransactionItem
from api.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=TransactionsListResponse,
    summary="Get recent transactions",
    description="Returns list of recent evaluated transactions with optional filtering by risk level or prediction."
)
def list_transactions(
    limit: int = Query(50, ge=1, le=500, description="Max number of transactions to retrieve"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: LOW, MEDIUM, HIGH"),
    prediction: Optional[int] = Query(None, description="Filter by fraud label: 0 (legitimate), 1 (fraud)"),
    service: ModelService = Depends(get_model_service)
) -> TransactionsListResponse:
    txs = service.get_recent_transactions(
        limit=limit,
        risk_level=risk_level,
        prediction=prediction
    )
    return TransactionsListResponse(
        total=len(txs),
        limit=limit,
        transactions=txs
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionItem,
    summary="Get transaction by ID",
    description="Retrieves details for a specific transaction."
)
def get_transaction_by_id(
    transaction_id: str,
    service: ModelService = Depends(get_model_service)
) -> TransactionItem:
    txs = service.get_recent_transactions(limit=1000)
    for tx in txs:
        if tx.transaction_id == transaction_id:
            return tx
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Transaction '{transaction_id}' not found"
    )

