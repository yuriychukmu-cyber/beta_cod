from abc import ABC, abstractmethod
from datssol.game.commands import TurnCommand
from datssol.game.state import WorldState


class Bot(ABC):
    @abstractmethod
    def act(self, state: WorldState, player_id: int) -> TurnCommand:
        raise NotImplementedError
