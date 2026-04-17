import torch
from torch import nn
from torch.optim import Adam
from datssol.train.losses import ppo_loss


class MAPPOTrainer:
    def __init__(self, actor: nn.Module, critic: nn.Module, lr: float = 3e-4) -> None:
        self.actor = actor
        self.critic = critic
        self.opt = Adam(list(actor.parameters()) + list(critic.parameters()), lr=lr)

    def update(self, ratio: torch.Tensor, adv: torch.Tensor, values: torch.Tensor, returns: torch.Tensor, entropy: torch.Tensor) -> dict[str, float]:
        pol = ppo_loss(ratio, adv)
        val = ((values - returns) ** 2).mean()
        ent = -entropy.mean()
        loss = pol + 0.5 * val + 0.01 * ent
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()
        return {"loss": float(loss.item()), "policy": float(pol.item()), "value": float(val.item())}
