from dataclasses import dataclass
import torch
from torch import nn
from datssol.constants import ACTION_TYPES, UPGRADE_TYPES


@dataclass(slots=True)
class ModelOutput:
    action_logits: torch.Tensor
    exit_logits: torch.Tensor
    target_logits: torch.Tensor
    local_priority: torch.Tensor
    local_utility: torch.Tensor
    upgrade_logits: torch.Tensor
    relocate_logits: torch.Tensor
    value: torch.Tensor
    aux_risks: torch.Tensor


class PolicyHeads(nn.Module):
    def __init__(self, hidden: int, max_targets: int = 64) -> None:
        super().__init__()
        self.action = nn.Linear(hidden, len(ACTION_TYPES))
        self.exit = nn.Linear(hidden, 1)
        self.target = nn.Linear(hidden, max_targets)
        self.priority = nn.Linear(hidden, 1)
        self.utility = nn.Linear(hidden, 1)
        self.upgrade = nn.Linear(hidden, len(UPGRADE_TYPES))
        self.relocate = nn.Linear(hidden, max_targets)
        self.value = nn.Linear(hidden, 1)
        self.risks = nn.Linear(hidden, 4)

    def forward(self, node_h: torch.Tensor, global_h: torch.Tensor) -> ModelOutput:
        return ModelOutput(
            action_logits=self.action(node_h),
            exit_logits=self.exit(node_h).squeeze(-1),
            target_logits=self.target(node_h),
            local_priority=self.priority(node_h).squeeze(-1),
            local_utility=self.utility(node_h).squeeze(-1),
            upgrade_logits=self.upgrade(global_h),
            relocate_logits=self.relocate(global_h),
            value=self.value(global_h).squeeze(-1),
            aux_risks=self.risks(global_h),
        )
