# Training

## Imitation
- Generate trajectories from heuristic-vs-heuristic self-play (`generate_dataset.py`).
- Convert to graph-like tabular tensors.
- Train multitask heads with cross-entropy + MSE.
- Fast practical path for tomorrow's stronger bot:
  1. `python -m datssol.scripts.offline_finetune --episodes 16 --turns 80 --epochs 3`
  2. deploy checkpoint with `NeuralBot(checkpoint=...)`
  3. run planner-based inference against mock/real API.

## RL scaffold (MAPPO-style)
- Shared actor over controllable plantations.
- Centralized critic over global summary.
- Rollout storage with GAE and PPO clipped objective.
- Invalid action masking respected in action selection.
