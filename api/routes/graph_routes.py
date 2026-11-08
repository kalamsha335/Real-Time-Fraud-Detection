from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from graph.graph_analysis import GraphAnalysisService, get_graph_service
from api.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="/graph", tags=["Graph Analysis (PyTorch Geometric)"])


@router.get(
    "/analysis",
    summary="Get transaction relationship graph and GCN analysis",
    description="Constructs graph topology from recent transactions, computes connectivity statistics, and runs GCN inference."
)
def get_graph_analysis(
    limit: int = Query(50, ge=5, le=200, description="Number of recent transactions to analyze"),
    graph_service: GraphAnalysisService = Depends(get_graph_service),
    model_service: ModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    txs = model_service.get_recent_transactions(limit=limit)
    records = []
    for tx in txs:
        rec = {
            "TransactionID": tx.transaction_id,
            "TransactionAmt": tx.amount,
            "card1": tx.card1,
            "ProductCD": tx.product_cd
        }
        if tx.features_preview:
            rec.update(tx.features_preview)
        records.append(rec)

    return graph_service.analyze_transaction_network(records)
