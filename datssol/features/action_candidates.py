from datssol.types import LocalAction
from datssol.game.state import WorldState
from datssol.utils.geometry import ortho_neighbors


def local_action_candidates(state: WorldState, player_id: int, top_k: int = 4) -> dict[int, list[LocalAction]]:
    out: dict[int, list[LocalAction]] = {}
    enemies = [p for p in state.plantations.values() if p.owner_id != player_id]
    beavers = list(state.beaver_lairs.values())
    for p in state.plantations.values():
        if p.owner_id != player_id or not p.connected_to_main:
            continue
        cands = [LocalAction(author_id=p.id, exit_id=p.id, action_type="noop", target=None, score=0.0)]
        for n in ortho_neighbors(p.pos, state.width, state.height):
            if n not in state.mountains and not any(o.pos == n for o in state.plantations.values()):
                cands.append(LocalAction(p.id, p.id, "build", n, 0.2))
        for e in enemies:
            if abs(e.pos[0] - p.pos[0]) <= 2 and abs(e.pos[1] - p.pos[1]) <= 2:
                cands.append(LocalAction(p.id, p.id, "sabotage", e.id, 0.5))
        for b in beavers:
            if abs(b.pos[0] - p.pos[0]) <= 2 and abs(b.pos[1] - p.pos[1]) <= 2:
                cands.append(LocalAction(p.id, p.id, "attack_beaver", b.id, 0.4))
        own_repair = [q for q in state.plantations.values() if q.owner_id == player_id and q.id != p.id and q.hp < 40]
        if own_repair:
            cands.append(LocalAction(p.id, p.id, "repair", own_repair[0].id, 0.6))
        out[p.id] = sorted(cands, key=lambda x: x.score, reverse=True)[:top_k]
    return out
