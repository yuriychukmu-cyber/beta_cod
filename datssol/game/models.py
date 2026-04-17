from dataclasses import dataclass, field
from datssol.types import Point
from datssol.constants import GC


@dataclass(slots=True)
class PlayerStats:
    player_id: int
    score: float = 0.0
    upgrade_bank: int = 0
    upgrades: dict[str, int] = field(default_factory=dict)
    main_id: int | None = None


@dataclass(slots=True)
class Plantation:
    id: int
    owner_id: int
    pos: Point
    hp: float = GC.base_mhp
    created_turn: int = 0
    connected_to_main: bool = True
    immune_until_turn: int = 0


@dataclass(slots=True)
class Construction:
    owner_id: int
    pos: Point
    progress: float = 0.0
    hp: float = GC.base_mhp
    last_progress_turn: int = -1


@dataclass(slots=True)
class BeaverLair:
    id: int
    pos: Point
    hp: float = GC.beaver_lair_hp


@dataclass(slots=True)
class WeatherState:
    sandstorm_active: bool = False
    sandstorm_age: int = 0
    sandstorm_center: Point | None = None
