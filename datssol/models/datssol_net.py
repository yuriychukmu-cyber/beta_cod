import torch
from torch import nn
from datssol.models.graph_encoder import make_graph_encoder
from datssol.models.temporal import TemporalGRU
from datssol.models.heads import ModelOutput, PolicyHeads


class DatsSolNet(nn.Module):
    def __init__(self, in_dim: int = 5, hidden: int = 64, history_dim: int = 64) -> None:
        super().__init__()
        self.encoder = make_graph_encoder(in_dim, hidden)
        self.temporal = TemporalGRU(history_dim)
        self.history_proj = nn.Linear(hidden, history_dim)
        self.combine = nn.Linear(hidden + history_dim, hidden)
        self.heads = PolicyHeads(hidden)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, history: torch.Tensor | None = None) -> ModelOutput:
        node_h = self.encoder(x, edge_index)
        global_h = node_h.mean(dim=0, keepdim=True)
        if history is None:
            hist = torch.zeros((1, 1, self.history_proj.out_features), device=x.device)
        else:
            hist = history
        _, h = self.temporal(hist)
        h_last = h[-1]
        expanded = h_last.expand(node_h.size(0), -1)
        node_fused = torch.relu(self.combine(torch.cat([node_h, expanded], dim=-1)))
        global_fused = node_fused.mean(dim=0, keepdim=True)
        return self.heads(node_fused, global_fused)
