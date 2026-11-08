import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from torch_geometric.data import Data

logger = logging.getLogger("graph_builder")
logging.basicConfig(level=logging.INFO)

GRAPH_FEATURE_COLUMNS = [
    "TransactionAmt",
    "TransactionDT",
    "C1",
    "C2",
    "D1",
    "D2",
    "V258",
    "V264",
    "previous_card_transactions",
    "previous_avg_amount",
    "previous_transactions_24h"
]


class TransactionGraphBuilder:
    """
    Constructs PyTorch Geometric transaction graph structures from tabular transaction events,
    linking nodes through anonymized card1 relationship proxies.
    """

    def __init__(self):
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.is_fitted = False

    def prepare_graph_dataframe(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Derive the 11 graph features and temporal relationship proxies."""
        df = pd.DataFrame(records).copy()

        # Fill essential identification columns
        if "TransactionID" not in df.columns:
            df["TransactionID"] = [f"TX-{i}" for i in range(len(df))]
        if "TransactionDT" not in df.columns:
            df["TransactionDT"] = np.arange(len(df)) * 60
        if "TransactionAmt" not in df.columns:
            df["TransactionAmt"] = 50.0
        if "card1" not in df.columns:
            df["card1"] = 1000

        # Ensure numeric types for core fields
        df["TransactionDT"] = pd.to_numeric(df["TransactionDT"], errors="coerce").fillna(0)
        df["TransactionAmt"] = pd.to_numeric(df["TransactionAmt"], errors="coerce").fillna(0.0)
        df["card1"] = pd.to_numeric(df["card1"], errors="coerce").fillna(0).astype(int)

        # Sort chronologically
        df = df.sort_values(["TransactionDT"]).reset_index(drop=True)

        # Compute relationship velocity proxy features
        df["previous_card_transactions"] = df.groupby("card1").cumcount()
        df["previous_avg_amount"] = (
            df.groupby("card1")["TransactionAmt"]
            .transform(lambda s: s.shift(1).expanding().mean())
            .fillna(df["TransactionAmt"])
        )

        # Previous 24h count per card1
        counts_24h = []
        for card, group in df.groupby("card1", sort=False):
            times = group["TransactionDT"].to_numpy()
            positions = np.arange(len(times))
            idx_24h = np.searchsorted(times, times - 86400, side="left")
            counts_24h.extend(np.maximum(0, positions - idx_24h))
        df["previous_transactions_24h"] = np.array(counts_24h, dtype=np.int64)

        # Ensure other required numerical columns exist
        for col in ["C1", "C2", "D1", "D2", "V258", "V264"]:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        return df

    def build_pyg_data(self, records: List[Dict[str, Any]]) -> Tuple[Data, Dict[str, Any]]:
        """
        Builds a PyTorch Geometric Data object with directed edges connecting consecutive
        transactions sharing card1 attributes.
        """
        df = self.prepare_graph_dataframe(records)
        num_nodes = len(df)

        if num_nodes == 0:
            empty_x = torch.empty((0, len(GRAPH_FEATURE_COLUMNS)), dtype=torch.float32)
            empty_edges = torch.empty((2, 0), dtype=torch.long)
            return Data(x=empty_x, edge_index=empty_edges), {"total_nodes": 0, "total_edges": 0}

        # Extract features
        X_df = df[GRAPH_FEATURE_COLUMNS].copy()
        if not self.is_fitted:
            X_imputed = self.imputer.fit_transform(X_df)
            X_scaled = self.scaler.fit_transform(X_imputed)
            self.is_fitted = True
        else:
            X_imputed = self.imputer.transform(X_df)
            X_scaled = self.scaler.transform(X_imputed)

        x_tensor = torch.tensor(X_scaled, dtype=torch.float32)

        # Construct directed temporal edges by shared card1 proxy
        src_nodes = []
        dst_nodes = []
        for card, group in df.groupby("card1", sort=False):
            indices = group.index.to_numpy()
            if len(indices) > 1:
                src_nodes.extend(indices[:-1])
                dst_nodes.extend(indices[1:])

        if src_nodes:
            edge_index = torch.tensor([src_nodes, dst_nodes], dtype=torch.long)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)

        # Extract target labels if present
        if "isFraud" in df.columns:
            y = torch.tensor(df["isFraud"].fillna(0).astype(int).to_numpy(), dtype=torch.long)
        else:
            y = None

        data = Data(x=x_tensor, edge_index=edge_index, y=y)
        data.transaction_ids = df["TransactionID"].tolist()
        data.card1 = df["card1"].tolist()
        data.amounts = df["TransactionAmt"].tolist()

        # Compute graph connectivity statistics
        unique_cards = df["card1"].nunique()
        degrees = np.bincount(src_nodes, minlength=num_nodes) if src_nodes else np.zeros(num_nodes)
        avg_degree = float(np.mean(degrees))
        max_group_size = int(df["card1"].value_counts().max()) if num_nodes > 0 else 0

        stats = {
            "total_nodes": num_nodes,
            "total_directed_edges": int(edge_index.size(1)),
            "unique_relationship_anchors": unique_cards,
            "average_degree": round(avg_degree, 2),
            "max_cluster_size": max_group_size,
            "connected_pairs_count": len(src_nodes)
        }

        return data, stats

    def to_visualization_json(self, data: Data, max_nodes: int = 100) -> Dict[str, Any]:
        """Convert PyG data to D3 / React graph visualization format."""
        nodes = []
        total = min(data.x.size(0), max_nodes)

        for i in range(total):
            tx_id = data.transaction_ids[i] if hasattr(data, "transaction_ids") else f"TX-{i}"
            card = data.card1[i] if hasattr(data, "card1") else 0
            amt = data.amounts[i] if hasattr(data, "amounts") else 0.0
            nodes.append({
                "id": tx_id,
                "index": i,
                "card1": card,
                "amount": round(float(amt), 2),
                "is_hub": False
            })

        links = []
        if data.edge_index is not None and data.edge_index.size(1) > 0:
            edges = data.edge_index.numpy()
            for src, dst in zip(edges[0], edges[1]):
                if src < total and dst < total:
                    links.append({
                        "source": nodes[src]["id"],
                        "target": nodes[dst]["id"],
                        "relationship": "shared_card1_proxy"
                    })

        # Tag hub nodes
        deg_map = {}
        for l in links:
            deg_map[l["source"]] = deg_map.get(l["source"], 0) + 1
        for n in nodes:
            if deg_map.get(n["id"], 0) >= 2:
                n["is_hub"] = True

        return {
            "nodes": nodes,
            "links": links,
            "total_nodes": len(nodes),
            "total_links": len(links),
            "note": "Edges represent shared anonymized card1 relationship proxies, not confirmed fraud rings."
        }
