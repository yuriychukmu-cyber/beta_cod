from dataclasses import dataclass, field
import torch


@dataclass
class RolloutStorage:
    obs: list[torch.Tensor] = field(default_factory=list)
    actions: list[torch.Tensor] = field(default_factory=list)
    rewards: list[torch.Tensor] = field(default_factory=list)
    values: list[torch.Tensor] = field(default_factory=list)
    dones: list[torch.Tensor] = field(default_factory=list)

    def add(self, obs: torch.Tensor, action: torch.Tensor, reward: torch.Tensor, value: torch.Tensor, done: torch.Tensor) -> None:
        self.obs.append(obs)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.dones.append(done)

    def compute_gae(self, gamma: float = 0.99, lam: float = 0.95) -> tuple[torch.Tensor, torch.Tensor]:
        rews = torch.stack(self.rewards)
        vals = torch.stack(self.values)
        dones = torch.stack(self.dones)
        adv = torch.zeros_like(rews)
        gae = torch.zeros_like(rews[0])
        next_val = torch.zeros_like(vals[0])
        for t in reversed(range(len(rews))):
            delta = rews[t] + gamma * next_val * (1 - dones[t]) - vals[t]
            gae = delta + gamma * lam * (1 - dones[t]) * gae
            adv[t] = gae
            next_val = vals[t]
        return adv, adv + vals
