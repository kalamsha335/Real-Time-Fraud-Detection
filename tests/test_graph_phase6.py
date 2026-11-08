import unittest
import os
import sys
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from graph.gnn_model import FraudGCN
from graph.graph_builder import TransactionGraphBuilder
from graph.graph_analysis import GraphAnalysisService


class TestPhase6GraphAnalysis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.builder = TransactionGraphBuilder()
        cls.service = GraphAnalysisService()

        # Create mock transactions with intentional shared card1 relationships
        cls.mock_txs = [
            {"TransactionID": "TX-G1", "TransactionDT": 100, "TransactionAmt": 150.0, "card1": 5001, "C1": 1.0, "D1": 2.0},
            {"TransactionID": "TX-G2", "TransactionDT": 200, "TransactionAmt": 250.0, "card1": 5001, "C1": 1.0, "D1": 2.0},
            {"TransactionID": "TX-G3", "TransactionDT": 300, "TransactionAmt": 350.0, "card1": 5001, "C1": 2.0, "D1": 3.0},
            {"TransactionID": "TX-G4", "TransactionDT": 400, "TransactionAmt": 50.0,  "card1": 5002, "C1": 1.0, "D1": 0.0},
            {"TransactionID": "TX-G5", "TransactionDT": 500, "TransactionAmt": 75.0,  "card1": 5002, "C1": 1.0, "D1": 1.0},
        ]

    def test_01_gcn_architecture(self):
        """Verify FraudGCN module structure."""
        gcn = FraudGCN(input_features=11, hidden_features=32, num_classes=2)
        x = torch.randn((5, 11))
        edge_index = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)
        logits = gcn(x, edge_index)

        self.assertEqual(logits.shape, (5, 2))
        probs = gcn.predict_proba(x, edge_index)
        self.assertEqual(probs.shape, (5,))
        self.assertTrue((probs >= 0.0).all() and (probs <= 1.0).all())

    def test_02_graph_builder_pyg_data_and_edges(self):
        """Verify graph construction connects shared card1 transactions."""
        pyg_data, stats = self.builder.build_pyg_data(self.mock_txs)
        self.assertEqual(pyg_data.x.shape, (5, 11))
        # card1=5001 has 3 nodes -> 2 directed edges; card1=5002 has 2 nodes -> 1 directed edge; total = 3 edges
        self.assertEqual(pyg_data.edge_index.shape[1], 3)
        self.assertEqual(stats["total_nodes"], 5)
        self.assertEqual(stats["total_directed_edges"], 3)
        self.assertEqual(stats["unique_relationship_anchors"], 2)
        self.assertEqual(stats["max_cluster_size"], 3)

    def test_03_graph_analysis_service(self):
        """Verify comprehensive graph analysis and topology visualization structure."""
        report = self.service.analyze_transaction_network(self.mock_txs)
        self.assertEqual(report["status"], "success")
        self.assertIn("network_topology", report)
        self.assertIn("nodes", report["network_topology"])
        self.assertIn("links", report["network_topology"])
        self.assertEqual(len(report["network_topology"]["nodes"]), 5)
        self.assertEqual(len(report["network_topology"]["links"]), 3)
        self.assertIn("disclaimer", report)

    def test_04_score_fusion_policy(self):
        """Verify explicit, configurable risk score fusion formula."""
        xgb_score = 0.80
        gcn_score = 0.40
        weight = 0.15

        # Expected: 0.85 * 0.80 + 0.15 * 0.40 = 0.68 + 0.06 = 0.74
        fused = self.service.fuse_risk_scores(xgb_score, gcn_score, graph_weight=weight)
        self.assertAlmostEqual(fused, 0.74, places=2)

        # Zero weight returns pure XGBoost
        pure_xgb = self.service.fuse_risk_scores(xgb_score, gcn_score, graph_weight=0.0)
        self.assertEqual(pure_xgb, 0.80)


if __name__ == "__main__":
    unittest.main()
