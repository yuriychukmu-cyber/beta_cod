from collections import deque
from datssol.game.state import WorldState
from datssol.utils.geometry import ortho_neighbors


def update_connectivity(state: WorldState, player_id: int) -> None:
    player = state.players[player_id]
    main_id = player.main_id
    own = {p.id: p for p in state.plantations.values() if p.owner_id == player_id}
    for p in own.values():
        p.connected_to_main = False
    if main_id is None or main_id not in own:
        return
    by_pos = {p.pos: p.id for p in own.values()}
    q = deque([main_id])
    own[main_id].connected_to_main = True
    while q:
        cur = own[q.popleft()]
        for npos in ortho_neighbors(cur.pos, state.width, state.height):
            nid = by_pos.get(npos)
            if nid is not None and not own[nid].connected_to_main:
                own[nid].connected_to_main = True
                q.append(nid)


def update_all_connectivity(state: WorldState) -> None:
    for pid in list(state.players):
        update_connectivity(state, pid)
