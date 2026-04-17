from dataclasses import dataclass

from datssol.bots.base import Bot
from datssol.constants import GC
from datssol.game.commands import PlantationCommand, TurnCommand
from datssol.game.state import WorldState
from datssol.types import Point
from datssol.utils.geometry import in_square_radius


@dataclass(slots=True)
class HeuristicWeights:
    boosted_cell_bonus: float = 30.0
    near_completion_bonus: float = 20.0
    construction_existing_progress_weight: float = 2.0
    enemy_kill_bonus: float = 60.0
    enemy_pressure_bonus: float = 12.0
    beaver_kill_bonus: float = 80.0
    repair_main_bonus: float = 50.0


class HeuristicBot(Bot):
    """Greedy score-maximizing baseline with explicit anti-empty-turn behavior."""

    def __init__(self, weights: HeuristicWeights | None = None) -> None:
        self.w = weights or HeuristicWeights()

    @staticmethod
    def _is_boosted(cell: Point) -> bool:
        return cell[0] % GC.boosted_modulo == 0 and cell[1] % GC.boosted_modulo == 0

    def _best_upgrade(self, state: WorldState, player_id: int) -> str | None:
        p = state.players[player_id]
        if p.upgrade_bank <= 0:
            return None
        own = [q for q in state.plantations.values() if q.owner_id == player_id]
        low_hp = sum(1 for q in own if q.hp < 20)
        if low_hp > 0:
            return "repair_power"
        if len(own) > 24:
            return "settlement_limit"
        if p.upgrades.get("max_hp", 0) < 3:
            return "max_hp"
        if p.upgrades.get("signal_range", 0) < 2:
            return "signal_range"
        return "vision_range"

    def _build_target_score(self, state: WorldState, player_id: int, author_pos: Point, target: Point) -> float:
        if target in state.mountains:
            return -1e9
        if any(p.pos == target for p in state.plantations.values()):
            return -1e9
        boosted = self.w.boosted_cell_bonus if self._is_boosted(target) else 0.0
        terraform = state.terraforming.get(target, 0.0)
        near_completion = self.w.near_completion_bonus if terraform >= 85.0 else 0.0
        own_progress = state.constructions.get((player_id, target))
        progress_bonus = self.w.construction_existing_progress_weight * (own_progress.progress if own_progress else 0.0)
        center_bias = -0.02 * abs(target[0] - state.width // 2) - 0.02 * abs(target[1] - state.height // 2)
        return boosted + near_completion + progress_bonus + center_bias

    def _best_build_target(self, state: WorldState, player_id: int, exit_pos: Point) -> Point | None:
        best: Point | None = None
        best_score = -1e9
        for x in range(max(0, exit_pos[0] - GC.base_ar), min(state.width, exit_pos[0] + GC.base_ar + 1)):
            for y in range(max(0, exit_pos[1] - GC.base_ar), min(state.height, exit_pos[1] + GC.base_ar + 1)):
                target = (x, y)
                score = self._build_target_score(state, player_id, exit_pos, target)
                if score > best_score:
                    best_score = score
                    best = target
        return best

    def act(self, state: WorldState, player_id: int) -> TurnCommand:
        own = [p for p in state.plantations.values() if p.owner_id == player_id and p.connected_to_main]
        if not own:
            return TurnCommand(player_id=player_id, upgrade=self._best_upgrade(state, player_id))

        own_by_id = {p.id: p for p in own}
        main_id = state.players[player_id].main_id
        main = own_by_id.get(main_id) if main_id is not None else None

        actions: list[PlantationCommand] = []
        enemies = [e for e in state.plantations.values() if e.owner_id != player_id]
        beavers = list(state.beaver_lairs.values())

        # 1) protect main / relocate if critical
        relocate_to: int | None = None
        if main is not None and main.hp < 14:
            defenders = sorted([q for q in own if q.id != main.id and in_square_radius(q.pos, main.pos, GC.base_ar)], key=lambda p: p.hp, reverse=True)
            if defenders:
                actions.append(PlantationCommand(author_id=defenders[0].id, exit_id=defenders[0].id, target=main.id))
            neighbors = [q for q in own if q.id != main.id and abs(q.pos[0] - main.pos[0]) + abs(q.pos[1] - main.pos[1]) == 1 and q.hp > main.hp + 8]
            if neighbors:
                relocate_to = neighbors[0].id

        # 2) greedy per-plantation action
        for p in sorted(own, key=lambda q: (q.id != main_id, q.hp), reverse=True):
            # avoid overly aggressive attacks if main is weak
            main_is_weak = main is not None and main.hp < 18

            # enemy sabotage priority: killshots first
            kill_targets = [e for e in enemies if in_square_radius(p.pos, e.pos, GC.base_ar) and e.hp <= GC.base_se]
            if kill_targets and not main_is_weak:
                target = min(kill_targets, key=lambda e: e.hp)
                actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=target.id))
                continue

            # beaver last-hit / elimination is high value
            beaver_targets = [b for b in beavers if in_square_radius(p.pos, b.pos, GC.base_ar)]
            if beaver_targets:
                target_b = min(beaver_targets, key=lambda b: b.hp)
                if target_b.hp <= GC.base_be + 2:
                    actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=target_b.id))
                    continue

            # repair own critical non-main plantations
            damaged = [q for q in own if q.id != p.id and q.hp < 20]
            if damaged:
                target_r = min(damaged, key=lambda q: q.hp)
                if in_square_radius(p.pos, target_r.pos, GC.base_ar):
                    actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=target_r.id))
                    continue

            # build greedily toward boosted/valuable cells
            target_build = self._best_build_target(state, player_id, p.pos)
            if target_build is not None:
                actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=target_build))
                continue

            # fallback pressure on nearest enemy
            enemy_targets = [e for e in enemies if in_square_radius(p.pos, e.pos, GC.base_ar)]
            if enemy_targets and not main_is_weak:
                actions.append(PlantationCommand(author_id=p.id, exit_id=p.id, target=min(enemy_targets, key=lambda e: e.hp).id))

        # avoid empty command server rejection
        upgrade = self._best_upgrade(state, player_id)
        if not actions and upgrade is None and relocate_to is None and own:
            # deterministic no-op equivalent via low-impact build attempt to nearest legal empty cell
            fallback_target = self._best_build_target(state, player_id, own[0].pos)
            if fallback_target is not None:
                actions.append(PlantationCommand(author_id=own[0].id, exit_id=own[0].id, target=fallback_target))

        return TurnCommand(player_id=player_id, actions=actions, upgrade=upgrade, relocate_main_to=relocate_to)
