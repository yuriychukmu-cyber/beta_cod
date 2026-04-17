import random
from datssol.bots.base import Bot
from datssol.game.commands import PlantationCommand, TurnCommand
from datssol.game.state import WorldState


class RandomBot(Bot):
    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def act(self, state: WorldState, player_id: int) -> TurnCommand:
        own = [p for p in state.plantations.values() if p.owner_id == player_id and p.connected_to_main]
        actions: list[PlantationCommand] = []
        for p in own:
            if self.rng.random() < 0.5:
                target = (max(0, min(state.width - 1, p.pos[0] + self.rng.choice([-1, 0, 1]))), max(0, min(state.height - 1, p.pos[1] + self.rng.choice([-1, 0, 1]))))
                actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=target))
        return TurnCommand(player_id=player_id, actions=actions)
