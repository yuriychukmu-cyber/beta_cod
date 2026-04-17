from dataclasses import dataclass
import numpy as np
import torch
from torch.utils.data import Dataset


@dataclass(slots=True)
class TrajectoryBatch:
    x: torch.Tensor
    action: torch.Tensor


class ImitationDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, npz_path: str) -> None:
        data = np.load(npz_path)
        self.x = data["x"].astype(np.float32)
        self.y = data["y"].astype(np.int64)

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return torch.from_numpy(self.x[idx]), torch.tensor(self.y[idx])
