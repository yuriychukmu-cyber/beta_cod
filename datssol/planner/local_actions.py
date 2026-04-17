from datssol.features.action_candidates import local_action_candidates
from datssol.game.state import WorldState
from datssol.types import LocalAction


def topk_local_actions(state: WorldState, player_id: int, k: int = 4) -> dict[int, list[LocalAction]]:
    return local_action_candidates(state, player_id, top_k=k)
