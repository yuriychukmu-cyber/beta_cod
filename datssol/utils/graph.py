from datssol.game.state import WorldState


def build_world_adjacency(state: WorldState) -> dict[int, list[int]]:
    by_pos = {p.pos: p.id for p in state.plantations.values()}
    out: dict[int, list[int]] = {p.id: [] for p in state.plantations.values()}
    for p in state.plantations.values():
        x, y = p.pos
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q in by_pos:
                out[p.id].append(by_pos[q])
    return out
