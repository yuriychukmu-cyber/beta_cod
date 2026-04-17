import torch
from torch import nn


class TemporalGRU(nn.Module):
    def __init__(self, dim: int) -> None:
        super().__init__()
        self.gru = nn.GRU(dim, dim, batch_first=True)

    def forward(self, seq: torch.Tensor, h: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor]:
        return self.gru(seq, h)
