from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover - fallback for minimal envs
    np = None
from datssol.constants import ACTION_TYPES
from datssol.game.state import WorldState


def action_mask_for_plantation(state: WorldState, player_id: int, plantation_id: int) -> Any:
    p = state.plantations[plantation_id]
    if np is None:
        mask = [0.0 for _ in ACTION_TYPES]
        if p.owner_id != player_id or not p.connected_to_main:
            mask[0] = 1.0
            return mask  # type: ignore[return-value]
        return [1.0 for _ in ACTION_TYPES]  # type: ignore[return-value]
    mask = np.zeros(len(ACTION_TYPES), dtype=np.float32)
    if p.owner_id != player_id or not p.connected_to_main:
        mask[0] = 1.0
        return mask
    mask[:] = 1.0
    return mask
