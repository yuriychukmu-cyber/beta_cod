from datssol.game.commands import PlantationCommand, TurnCommand
from datssol.game.state import WorldState
from datssol.planner.beam_search import build_turn_with_beam
from datssol.planner.local_actions import topk_local_actions
from datssol.planner.risk import estimate_isolation_risk, estimate_main_death_risk


class TurnPlanner:
    def __init__(self, beam_size: int = 8, top_k: int = 4) -> None:
        self.beam_size = beam_size
        self.top_k = top_k

    def plan(self, state: WorldState, player_id: int, model_output: object | None = None) -> TurnCommand:
        cand = topk_local_actions(state, player_id, self.top_k)
        picked = build_turn_with_beam(cand, self.beam_size)
        main_risk = estimate_main_death_risk(state, player_id)
        iso_risk = estimate_isolation_risk(state, player_id)
        if main_risk > 0.7:
            picked = [a for a in picked if a.action_type != "sabotage"]
        if iso_risk > 0.4:
            picked = [a for a in picked if a.action_type in ("noop", "build", "repair")]
        actions = [PlantationCommand(author_id=a.author_id, exit_id=a.exit_id, target=a.target) for a in picked if a.action_type != "noop"]
        return TurnCommand(player_id=player_id, actions=actions)
