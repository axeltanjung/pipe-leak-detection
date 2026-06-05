import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GraphData:
    node_features: torch.Tensor
    edge_index: torch.Tensor
    edge_weights: Optional[torch.Tensor] = None
    labels: Optional[torch.Tensor] = None


class GraphConvLayer(nn.Module):
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        self.bias = nn.Parameter(torch.FloatTensor(out_features))
        nn.init.xavier_uniform_(self.weight)
        nn.init.zeros_(self.bias)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        degree = adj.sum(dim=1, keepdim=True).clamp(min=1)
        norm_adj = adj / degree
        support = torch.mm(x, self.weight)
        output = torch.mm(norm_adj, support)
        return output + self.bias


class GraphAttentionLayer(nn.Module):
    def __init__(self, in_features: int, out_features: int, n_heads: int = 4, dropout: float = 0.2):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = out_features // n_heads

        self.W = nn.Linear(in_features, out_features, bias=False)
        self.attention = nn.Parameter(torch.FloatTensor(n_heads, 2 * self.head_dim))
        self.leaky_relu = nn.LeakyReLU(0.2)
        self.dropout = nn.Dropout(dropout)

        nn.init.xavier_uniform_(self.attention)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        N = x.size(0)
        h = self.W(x).view(N, self.n_heads, self.head_dim)

        h_i = h.unsqueeze(2).expand(-1, -1, N, -1)
        h_j = h.unsqueeze(1).expand(-1, N, -1, -1).transpose(1, 2)

        attention_input = torch.cat([h_i, h_j], dim=-1)
        e = self.leaky_relu(
            (attention_input * self.attention.unsqueeze(1).unsqueeze(1)).sum(dim=-1)
        )

        mask = adj.unsqueeze(0).expand(self.n_heads, -1, -1) == 0
        e = e.masked_fill(mask, float("-inf"))

        attention_weights = F.softmax(e, dim=-1)
        attention_weights = self.dropout(attention_weights)

        h_prime = torch.bmm(attention_weights, h.transpose(0, 1))
        output = h_prime.transpose(0, 1).contiguous().view(N, -1)

        return output


class PipelineGNN(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        output_dim: int = 1,
        num_layers: int = 3,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.conv_layers = nn.ModuleList()
        self.batch_norms = nn.ModuleList()

        self.conv_layers.append(GraphConvLayer(input_dim, hidden_dim))
        self.batch_norms.append(nn.BatchNorm1d(hidden_dim))

        for _ in range(num_layers - 2):
            self.conv_layers.append(GraphConvLayer(hidden_dim, hidden_dim))
            self.batch_norms.append(nn.BatchNorm1d(hidden_dim))

        self.conv_layers.append(GraphConvLayer(hidden_dim, hidden_dim))
        self.batch_norms.append(nn.BatchNorm1d(hidden_dim))

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, output_dim),
            nn.Sigmoid(),
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        for conv, bn in zip(self.conv_layers, self.batch_norms):
            residual = x if x.size(-1) == conv.weight.size(-1) else None
            x = conv(x, adj)
            x = bn(x)
            x = F.relu(x)
            x = self.dropout(x)
            if residual is not None:
                x = x + residual

        return self.classifier(x)


class PipelineGraphBuilder:
    def __init__(self, n_pipelines: int = 20):
        self.n_pipelines = n_pipelines
        self.adjacency_matrix = self._build_pipeline_network()

    def _build_pipeline_network(self) -> np.ndarray:
        adj = np.zeros((self.n_pipelines, self.n_pipelines))
        for i in range(self.n_pipelines - 1):
            adj[i, i + 1] = 1
            adj[i + 1, i] = 1

        np.random.seed(42)
        for _ in range(self.n_pipelines // 3):
            i, j = np.random.choice(self.n_pipelines, 2, replace=False)
            adj[i, j] = 1
            adj[j, i] = 1

        np.fill_diagonal(adj, 1)
        return adj

    def build_graph_from_features(
        self, pipeline_features: Dict[str, np.ndarray]
    ) -> GraphData:
        node_features = []
        for pid in sorted(pipeline_features.keys()):
            node_features.append(pipeline_features[pid])
        node_features = np.array(node_features)

        adj_tensor = torch.FloatTensor(self.adjacency_matrix)
        feat_tensor = torch.FloatTensor(node_features)

        return GraphData(
            node_features=feat_tensor,
            edge_index=adj_tensor,
        )


class GNNLeakPredictor:
    def __init__(self, input_dim: int, hidden_dim: int = 64, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = PipelineGNN(
            input_dim=input_dim, hidden_dim=hidden_dim, output_dim=1
        ).to(self.device)
        self.graph_builder = PipelineGraphBuilder()

    def train(
        self,
        pipeline_features: Dict[str, np.ndarray],
        labels: np.ndarray,
        epochs: int = 100,
        learning_rate: float = 0.01,
    ) -> dict:
        graph = self.graph_builder.build_graph_from_features(pipeline_features)
        x = graph.node_features.to(self.device)
        adj = graph.edge_index.to(self.device)
        y = torch.FloatTensor(labels).unsqueeze(1).to(self.device)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=5e-4)
        criterion = nn.BCELoss()

        history = {"loss": [], "accuracy": []}

        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            predictions = self.model(x, adj)
            loss = criterion(predictions, y)
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                pred_labels = (predictions > 0.5).float()
                accuracy = (pred_labels == y).float().mean().item()

            history["loss"].append(loss.item())
            history["accuracy"].append(accuracy)

        return history

    def predict(self, pipeline_features: Dict[str, np.ndarray]) -> np.ndarray:
        graph = self.graph_builder.build_graph_from_features(pipeline_features)
        x = graph.node_features.to(self.device)
        adj = graph.edge_index.to(self.device)

        self.model.eval()
        with torch.no_grad():
            predictions = self.model(x, adj)

        return predictions.cpu().numpy().flatten()

    def get_node_risk_scores(self, pipeline_features: Dict[str, np.ndarray]) -> Dict[str, float]:
        predictions = self.predict(pipeline_features)
        pipeline_ids = sorted(pipeline_features.keys())
        return {pid: float(pred) for pid, pred in zip(pipeline_ids, predictions)}

    def save(self, path: str):
        torch.save({
            "model_state": self.model.state_dict(),
            "adjacency": self.graph_builder.adjacency_matrix,
        }, path)

    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.graph_builder.adjacency_matrix = checkpoint["adjacency"]
        self.model.eval()
