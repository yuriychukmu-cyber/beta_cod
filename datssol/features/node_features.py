from typing import Any
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from datssol.game.state import WorldState


def build_node_features(state: WorldState, player_id: int) -> tuple[Any, list[int]]:
    ids = []
    feats = []
    for p in state.plantations.values():
        ids.append(p.id)
        feats.append([
            p.pos[0] / max(1, state.width - 1),
            p.pos[1] / max(1, state.height - 1),
            p.hp / 100.0,
            1.0 if p.owner_id == player_id else 0.0,
            1.0 if p.connected_to_main else 0.0,
        ])
    if np is None:
        return feats, ids
    if not feats:
        return np.zeros((0, 5), dtype=np.float32), ids
    return np.array(feats, dtype=np.float32), ids
