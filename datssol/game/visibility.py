from dataclasses import dataclass
from datssol.game.state import WorldState
from datssol.utils.geometry import in_square_radius
from datssol.constants import GC


@dataclass(slots=True)
class Observation:
    player_id: int
    turn: int
    visible_plantation_ids: list[int]
    visible_constructions: list[tuple[int, tuple[int, int]]]
    visible_beavers: list[int]


def observe(state: WorldState, player_id: int) -> Observation:
    own = [p for p in state.plantations.values() if p.owner_id == player_id]
    visible_cells: set[tuple[int, int]] = set()
    for p in own:
        for x in range(max(0, p.pos[0] - GC.base_vr), min(state.width, p.pos[0] + GC.base_vr + 1)):
            for y in range(max(0, p.pos[1] - GC.base_vr), min(state.height, p.pos[1] + GC.base_vr + 1)):
                visible_cells.add((x, y))
    vp = [p.id for p in state.plantations.values() if p.pos in visible_cells]
    vc = [(c.owner_id, c.pos) for c in state.constructions.values() if c.pos in visible_cells]
    vb = [b.id for b in state.beaver_lairs.values() if any(in_square_radius(p.pos, b.pos, GC.base_vr) for p in own)]
    return Observation(player_id=player_id, turn=state.turn, visible_plantation_ids=vp, visible_constructions=vc, visible_beavers=vb)
