from dataclasses import dataclass, field
import random
from datssol.game.models import BeaverLair, Construction, Plantation, PlayerStats, WeatherState
from datssol.types import Point


@dataclass(slots=True)
class WorldState:
    width: int
    height: int
    turn: int = 0
    next_entity_id: int = 1
    mountains: set[Point] = field(default_factory=set)
    terraforming: dict[Point, float] = field(default_factory=dict)
    terraform_completed_turn: dict[Point, int] = field(default_factory=dict)
    players: dict[int, PlayerStats] = field(default_factory=dict)
    plantations: dict[int, Plantation] = field(default_factory=dict)
    constructions: dict[tuple[int, Point], Construction] = field(default_factory=dict)
    beaver_lairs: dict[int, BeaverLair] = field(default_factory=dict)
    weather: WeatherState = field(default_factory=WeatherState)
    rng_seed: int = 0

    def rng(self) -> random.Random:
        return random.Random(self.rng_seed + self.turn)

    def spawn_plantation(self, owner_id: int, pos: Point, *, created_turn: int | None = None) -> int:
        pid = self.next_entity_id
        self.next_entity_id += 1
        self.plantations[pid] = Plantation(id=pid, owner_id=owner_id, pos=pos, created_turn=self.turn if created_turn is None else created_turn)
        if self.players[owner_id].main_id is None:
            self.players[owner_id].main_id = pid
        return pid
