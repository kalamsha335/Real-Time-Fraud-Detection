import os
import logging
from typing import Dict, Any, List, Optional
import torch

from .gnn_model import FraudGCN
from .graph_builder import TransactionGraphBuilder

logger = logging.getLogger("graph_analysis")
logging.basicConfig(level=logging.INFO)


class GraphAnalysisService:
    """
    Orchestrates graph-based relationship analysis using PyTorch Geometric GCN
    and shared-attribute network topologies.
    """

    def __init__(self, gcn_weights_path: Optional[str] = None):
        self.builder = TransactionGraphBuilder()
        self.gcn_model = FraudGCN(input_features=11, hidden_features=32, num_classes=2)
        self.gcn_model.eval()
        self.fusion_weight = 0.15  # Default 15% weight to experimental graph score

        if gcn_weights_path and os.path.exists(gcn_weights_path):
            try:
                self.gcn_model.load_state_dict(torch.load(gcn_weights_path, map_location="cpu"))
                logger.info("Loaded GCN checkpoint from %s", gcn_weights_path)
            except Exception as e:
                logger.warning("Could not load GCN weights: %s", e)

    def analyze_transaction_network(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds the transaction graph from recent records, computes topology metrics,
        and runs experimental GCN inference.
        """
        if not transactions:
            return {
                "status": "empty",
                "statistics": {},
                "suspicious_indicators": [],
                "disclaimer": "IEEE-CIS dataset lacks real identity labels; card1 is an anonymized proxy."
            }

        pyg_data, stats = self.builder.build_pyg_data(transactions)

        # Execute GCN inference
        with torch.no_grad():
            if pyg_data.x.size(0) > 0:
                gcn_probs = self.gcn_model.predict_proba(pyg_data.x, pyg_data.edge_index).numpy().tolist()
            else:
                gcn_probs = []

        # Identify suspicious relationship indicators
        suspicious_indicators = []
        if stats["max_cluster_size"] > 4:
            suspicious_indicators.append({
                "type": "HIGH_CARD_VELOCITY_CLUSTER",
                "severity": "MEDIUM",
                "description": f"Identified shared card1 cluster with {stats['max_cluster_size']} transactions.",
                "note": "Proxy indicator only; does not confirm an organized ring."
            })

        if stats["connected_pairs_count"] > 10:
            suspicious_indicators.append({
                "type": "DENSE_TRANSACTION_NETWORK",
                "severity": "LOW",
                "description": f"{stats['connected_pairs_count']} directed temporal links detected across transactions."
            })

        viz_data = self.builder.to_visualization_json(pyg_data, max_nodes=50)

        return {
            "status": "success",
            "statistics": stats,
            "gcn_fraud_probabilities": gcn_probs[:10],
            "suspicious_indicators": suspicious_indicators,
            "network_topology": viz_data,
            "fusion_policy": {
                "graph_weight": self.fusion_weight,
                "formula": f"final_risk = (1.0 - {self.fusion_weight}) * xgb_score + {self.fusion_weight} * gcn_score",
                "status": "EXPERIMENTAL_UNVALIDATED"
            },
            "disclaimer": "Shared attributes (card1) are relationship proxies only. They do not constitute verified customer identities or confirmed fraud rings."
        }

    def fuse_risk_scores(self, xgb_score: float, gcn_score: float, graph_weight: Optional[float] = None) -> float:
        """
        Explicit, configurable score fusion combining primary XGBoost probability
        with experimental GCN graph topology probability.
        """
        w = graph_weight if graph_weight is not None else self.fusion_weight
        fused = (1.0 - w) * float(xgb_score) + w * float(gcn_score)
        return round(float(fused), 4)


_graph_service_instance: Optional[GraphAnalysisService] = None


def get_graph_service() -> GraphAnalysisService:
    global _graph_service_instance
    if _graph_service_instance is None:
        _graph_service_instance = GraphAnalysisService()
    return _graph_service_instance
