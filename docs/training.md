# Training

## Imitation
- Generate trajectories from heuristic-vs-heuristic self-play (`generate_dataset.py`).
- Convert to graph-like tabular tensors.
- Train multitask heads with cross-entropy + MSE.

## RL scaffold (MAPPO-style)
- Shared actor over controllable plantations.
- Centralized critic over global summary.
- Rollout storage with GAE and PPO clipped objective.
- Invalid action masking respected in action selection.
