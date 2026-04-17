from typing import Any
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from datssol.game.state import WorldState


def build_edges(state: WorldState, node_ids: list[int]) -> Any:
    id_to_idx = {pid: i for i, pid in enumerate(node_ids)}
    edges = []
    for a in state.plantations.values():
        for b in state.plantations.values():
            if a.id == b.id:
                continue
            if abs(a.pos[0] - b.pos[0]) + abs(a.pos[1] - b.pos[1]) == 1:
                edges.append((id_to_idx[a.id], id_to_idx[b.id]))
    if np is None:
        return edges
    return np.array(edges, dtype=np.int64) if edges else np.zeros((0, 2), dtype=np.int64)
