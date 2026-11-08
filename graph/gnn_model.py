import torch
import torch.nn.functional as F
from torch.nn import Linear
from torch_geometric.nn import GCNConv


class FraudGCN(torch.nn.Module):
    """
    Experimental Graph Convolutional Network (GCN) for transaction relationship analysis.
    Built on PyTorch Geometric, preserving the experimental architecture developed in
    the project notebook exploration.
    """

    def __init__(self, input_features: int = 11, hidden_features: int = 32, num_classes: int = 2):
        super().__init__()
        self.conv1 = GCNConv(input_features, hidden_features)
        self.conv2 = GCNConv(hidden_features, hidden_features)
        self.classifier = Linear(hidden_features, num_classes)

    def forward(self, x, edge_index=None):
        # Support PyG Data object or tuple of (x, edge_index)
        if edge_index is None and hasattr(x, "x") and hasattr(x, "edge_index"):
            edge_index = x.edge_index
            x = x.x

        if edge_index is None or edge_index.numel() == 0:
            # Degenerate case when no edges exist in subgraph: self-loops
            num_nodes = x.size(0)
            edge_index = torch.arange(num_nodes, dtype=torch.long, device=x.device).repeat(2, 1)

        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.3, training=self.training)

        x = self.conv2(x, edge_index)
        x = F.relu(x)

        return self.classifier(x)

    def predict_proba(self, x, edge_index=None) -> torch.Tensor:
        """Returns softmax probabilities for binary fraud classification."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x, edge_index)
            probabilities = F.softmax(logits, dim=-1)
            return probabilities[:, 1]  # Return class 1 (fraud) probability
