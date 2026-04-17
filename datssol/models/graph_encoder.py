import torch
from torch import nn


class FallbackGraphEncoder(nn.Module):
    """Adjacency-based message passing without torch-geometric."""

    def __init__(self, in_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.node = nn.Linear(in_dim, hidden_dim)
        self.msg = nn.Linear(hidden_dim, hidden_dim)
        self.out = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = torch.relu(self.node(x))
        if edge_index.numel() > 0:
            src, dst = edge_index[:, 0], edge_index[:, 1]
            agg = torch.zeros_like(h)
            agg.index_add_(0, dst, self.msg(h[src]))
            h = h + agg
        return torch.relu(self.out(h))


def make_graph_encoder(in_dim: int, hidden_dim: int) -> nn.Module:
    return FallbackGraphEncoder(in_dim, hidden_dim)
