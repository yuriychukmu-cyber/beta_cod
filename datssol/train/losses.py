import torch
import torch.nn.functional as F


def imitation_loss(logits: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return F.cross_entropy(logits, y)


def ppo_loss(ratio: torch.Tensor, adv: torch.Tensor, clip_eps: float = 0.2) -> torch.Tensor:
    unclipped = ratio * adv
    clipped = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * adv
    return -torch.min(unclipped, clipped).mean()
