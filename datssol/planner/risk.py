from datssol.game.state import WorldState


def estimate_main_death_risk(state: WorldState, player_id: int) -> float:
    mid = state.players[player_id].main_id
    if mid is None or mid not in state.plantations:
        return 1.0
    hp = state.plantations[mid].hp
    return max(0.0, min(1.0, (20.0 - hp) / 20.0))


def estimate_isolation_risk(state: WorldState, player_id: int) -> float:
    own = [p for p in state.plantations.values() if p.owner_id == player_id]
    if not own:
        return 1.0
    iso = sum(1 for p in own if not p.connected_to_main)
    return iso / len(own)
