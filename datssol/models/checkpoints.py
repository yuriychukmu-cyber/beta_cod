import torch
from torch import nn


def save_checkpoint(model: nn.Module, path: str, extra: dict | None = None) -> None:
    payload = {"state_dict": model.state_dict(), "extra": extra or {}}
    torch.save(payload, path)


def load_checkpoint(model: nn.Module, path: str, map_location: str = "cpu") -> dict:
    payload = torch.load(path, map_location=map_location)
    model.load_state_dict(payload["state_dict"])
    return payload.get("extra", {})
