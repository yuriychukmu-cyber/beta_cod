from dataclasses import dataclass, field
from datssol.types import Point


@dataclass(slots=True)
class PlantationCommand:
    author_id: int
    exit_id: int
    target: Point | int | None


@dataclass(slots=True)
class TurnCommand:
    player_id: int
    actions: list[PlantationCommand] = field(default_factory=list)
    upgrade: str | None = None
    relocate_main_to: int | None = None
