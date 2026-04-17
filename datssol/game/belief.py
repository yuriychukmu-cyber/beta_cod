from dataclasses import dataclass, field
from datssol.game.visibility import Observation


@dataclass(slots=True)
class BeliefState:
    last_seen_plantations: dict[int, int] = field(default_factory=dict)
    ghost_beavers: set[int] = field(default_factory=set)

    def update(self, obs: Observation) -> None:
        for pid in obs.visible_plantation_ids:
            self.last_seen_plantations[pid] = obs.turn
        self.ghost_beavers.update(obs.visible_beavers)
