from dataclasses import dataclass
from typing import Literal

Point = tuple[int, int]
ActionType = Literal["noop", "build", "repair", "sabotage", "attack_beaver"]


@dataclass(slots=True)
class LocalAction:
    author_id: int
    exit_id: int
    action_type: ActionType
    target: Point | int | None
    score: float = 0.0


@dataclass(slots=True)
class PlannedTurn:
    player_id: int
    actions: list[LocalAction]
    upgrade: str | None = None
    relocate_main_to: int | None = None
