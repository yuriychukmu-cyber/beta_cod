from datssol.bots.base import Bot
from datssol.game.commands import PlantationCommand, TurnCommand
from datssol.game.state import WorldState
from datssol.utils.geometry import ortho_neighbors


class HeuristicBot(Bot):
    """Rule-based baseline prioritizing connectivity and safe expansion."""

    def act(self, state: WorldState, player_id: int) -> TurnCommand:
        own = [p for p in state.plantations.values() if p.owner_id == player_id and p.connected_to_main]
        actions: list[PlantationCommand] = []
        used_exits: set[int] = set()
        main = state.players[player_id].main_id

        for p in own:
            if p.id == main and p.hp < 20:
                allies = [q for q in own if q.id != p.id and abs(q.pos[0] - p.pos[0]) + abs(q.pos[1] - p.pos[1]) <= 2]
                if allies:
                    actions.append(PlantationCommand(author_id=allies[0].id, exit_id=allies[0].id, target=p.id))
                    used_exits.add(allies[0].id)
            enemy_targets = [e for e in state.plantations.values() if e.owner_id != player_id and abs(e.pos[0] - p.pos[0]) <= 2 and abs(e.pos[1] - p.pos[1]) <= 2]
            if enemy_targets and p.id not in used_exits:
                actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=enemy_targets[0].id))
                used_exits.add(p.id)
                continue
            for n in ortho_neighbors(p.pos, state.width, state.height):
                if any(o.pos == n for o in state.plantations.values()) or n in state.mountains:
                    continue
                if p.id not in used_exits:
                    actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=n))
                    used_exits.add(p.id)
                    break
        return TurnCommand(player_id=player_id, actions=actions)
