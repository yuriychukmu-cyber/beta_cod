from datssol.game.state import WorldState


def dense_reward(prev_score: float, new_score: float, main_alive: bool) -> float:
    bonus = 0.1 if main_alive else -1.0
    return (new_score - prev_score) / 100.0 + bonus


def player_main_alive(state: WorldState, player_id: int) -> bool:
    mid = state.players[player_id].main_id
    return mid in state.plantations
