"""Local DatsSol simulator with explicit phase order."""

from dataclasses import dataclass, field
from typing import Callable
import logging

from datssol.constants import GC
from datssol.game.commands import TurnCommand
from datssol.game.connectivity import update_all_connectivity
from datssol.game.state import WorldState
from datssol.game.models import BeaverLair, Construction, PlayerStats
from datssol.game.upgrades import effective_limit, effective_mhp, effective_rs
from datssol.utils.geometry import in_square_radius, ortho_neighbors
from datssol.utils.scoring import cell_score_cap

LOG = logging.getLogger(__name__)


@dataclass(slots=True)
class SimulatorConfig:
    width: int = 12
    height: int = 12
    players: int = 2
    seed: int = 7


@dataclass(slots=True)
class DatsSolSimulator:
    config: SimulatorConfig
    state: WorldState = field(init=False)

    def __post_init__(self) -> None:
        self.state = WorldState(width=self.config.width, height=self.config.height, rng_seed=self.config.seed)
        for pid in range(self.config.players):
            self.state.players[pid] = PlayerStats(player_id=pid)
            spawn = (0, pid) if pid % 2 == 0 else (self.config.width - 1, self.config.height - 1 - pid)
            self.state.spawn_plantation(pid, spawn)
        self.state.beaver_lairs[1] = BeaverLair(id=1, pos=(self.config.width // 2, self.config.height // 2))
        update_all_connectivity(self.state)

    def step(self, commands: dict[int, TurnCommand], exact_step: bool = True) -> WorldState:
        self._phase_upgrade(commands)
        self._phase_repair_build(commands)
        self._phase_sabotage(commands)
        self._phase_beaver_attack_by_players(commands)
        self._phase_relocate_main(commands)
        self._phase_beaver_attacks()
        self._phase_isolated_degrade()
        self._phase_stalled_constructions()
        self._phase_terraform_and_score()
        self._phase_respawn()
        self._phase_weather()
        self.state.turn += 1
        if self.state.turn % GC.upgrade_point_every_turns == 0:
            for player in self.state.players.values():
                player.upgrade_bank = min(GC.upgrade_max_bank, player.upgrade_bank + 1)
        return self.state

    def _exit_penalty(self, actions: list, idx: int) -> int:
        exit_id = actions[idx].exit_id
        prior = sum(1 for i in range(idx) if actions[i].exit_id == exit_id)
        return prior

    def _phase_upgrade(self, commands: dict[int, TurnCommand]) -> None:
        for pid, cmd in commands.items():
            if cmd.upgrade and self.state.players[pid].upgrade_bank > 0:
                self.state.players[pid].upgrade_bank -= 1
                self.state.players[pid].upgrades[cmd.upgrade] = self.state.players[pid].upgrades.get(cmd.upgrade, 0) + 1

    def _phase_repair_build(self, commands: dict[int, TurnCommand]) -> None:
        for pid, cmd in commands.items():
            for i, action in enumerate(cmd.actions):
                if action.author_id not in self.state.plantations or action.exit_id not in self.state.plantations:
                    continue
                author = self.state.plantations[action.author_id]
                exit_p = self.state.plantations[action.exit_id]
                if author.owner_id != pid or exit_p.owner_id != pid or not author.connected_to_main:
                    continue
                penalty = self._exit_penalty(cmd.actions, i)
                if isinstance(action.target, tuple):
                    target = action.target
                    if target in self.state.mountains or not in_square_radius(exit_p.pos, target, GC.base_ar):
                        continue
                    occ = any(p.pos == target for p in self.state.plantations.values())
                    if not occ:
                        key = (pid, target)
                        c = self.state.constructions.get(key, Construction(owner_id=pid, pos=target))
                        c.progress += max(0, GC.base_cs - penalty)
                        c.last_progress_turn = self.state.turn
                        self.state.constructions[key] = c
                        if c.progress >= GC.construction_threshold:
                            own = [p for p in self.state.plantations.values() if p.owner_id == pid]
                            if len(own) >= effective_limit(self.state.players[pid]):
                                oldest = min(own, key=lambda p: p.created_turn)
                                del self.state.plantations[oldest.id]
                            nid = self.state.spawn_plantation(pid, target)
                            self.state.plantations[nid].hp = effective_mhp(self.state.players[pid])
                            self.state.plantations[nid].immune_until_turn = self.state.turn + GC.new_plantation_immunity_turns
                            del self.state.constructions[key]
                elif isinstance(action.target, int) and action.target in self.state.plantations:
                    trg = self.state.plantations[action.target]
                    if trg.owner_id == pid and trg.id != author.id:
                        trg.hp = min(effective_mhp(self.state.players[pid]), trg.hp + max(0, effective_rs(self.state.players[pid]) - penalty))
        update_all_connectivity(self.state)

    def _phase_sabotage(self, commands: dict[int, TurnCommand]) -> None:
        pending_delete: list[int] = []
        for pid, cmd in commands.items():
            for i, action in enumerate(cmd.actions):
                if not isinstance(action.target, int) or action.target not in self.state.plantations:
                    continue
                if action.author_id not in self.state.plantations:
                    continue
                author = self.state.plantations[action.author_id]
                trg = self.state.plantations[action.target]
                if author.owner_id != pid or trg.owner_id == pid:
                    continue
                penalty = self._exit_penalty(cmd.actions, i)
                dmg = max(0, GC.base_se - penalty)
                if trg.immune_until_turn > self.state.turn:
                    continue
                trg.hp -= dmg
                if trg.hp <= 0:
                    pending_delete.append(trg.id)
                    self.state.players[pid].score += 10
        for t in pending_delete:
            self.state.plantations.pop(t, None)
        update_all_connectivity(self.state)

    def _phase_beaver_attack_by_players(self, commands: dict[int, TurnCommand]) -> None:
        for pid, cmd in commands.items():
            for i, action in enumerate(cmd.actions):
                if not isinstance(action.target, int) or action.target not in self.state.beaver_lairs:
                    continue
                if action.author_id not in self.state.plantations:
                    continue
                author = self.state.plantations[action.author_id]
                if author.owner_id != pid:
                    continue
                dmg = max(0, GC.base_be - self._exit_penalty(cmd.actions, i))
                self.state.beaver_lairs[action.target].hp -= dmg
                if self.state.beaver_lairs[action.target].hp <= 0:
                    self.state.players[pid].score += 100
                    del self.state.beaver_lairs[action.target]
                    break

    def _phase_relocate_main(self, commands: dict[int, TurnCommand]) -> None:
        for pid, cmd in commands.items():
            if cmd.relocate_main_to and cmd.relocate_main_to in self.state.plantations and self.state.plantations[cmd.relocate_main_to].owner_id == pid:
                self.state.players[pid].main_id = cmd.relocate_main_to
        update_all_connectivity(self.state)

    def _phase_beaver_attacks(self) -> None:
        for lair in self.state.beaver_lairs.values():
            lair.hp = min(GC.beaver_lair_hp, lair.hp + GC.beaver_lair_regen)
            for p in self.state.plantations.values():
                if in_square_radius(p.pos, lair.pos, GC.beaver_attack_range):
                    p.hp -= GC.beaver_attack_damage
            for c in self.state.constructions.values():
                if in_square_radius(c.pos, lair.pos, GC.beaver_attack_range):
                    c.hp -= GC.beaver_attack_damage
        for pid in [p.id for p in self.state.plantations.values() if p.hp <= 0]:
            self.state.plantations.pop(pid, None)

    def _phase_isolated_degrade(self) -> None:
        for p in self.state.plantations.values():
            if not p.connected_to_main:
                p.hp -= GC.base_ds
        for pid in [p.id for p in self.state.plantations.values() if p.hp <= 0]:
            self.state.plantations.pop(pid, None)

    def _phase_stalled_constructions(self) -> None:
        to_del = []
        for k, c in self.state.constructions.items():
            if c.last_progress_turn < self.state.turn:
                c.hp -= GC.stalled_construction_damage
            if c.hp <= 0:
                to_del.append(k)
        for k in to_del:
            del self.state.constructions[k]

    def _phase_terraform_and_score(self) -> None:
        to_delete = []
        for p in self.state.plantations.values():
            cur = self.state.terraforming.get(p.pos, 0.0)
            cur = min(100.0, cur + GC.base_ts)
            self.state.terraforming[p.pos] = cur
            cap = cell_score_cap(p.pos)
            self.state.players[p.owner_id].score += cap * (GC.base_ts / 100.0)
            if cur >= 100.0:
                self.state.terraform_completed_turn[p.pos] = self.state.turn
                to_delete.append(p.id)
        for pid in to_delete:
            self.state.plantations.pop(pid, None)
        for cell, tdone in list(self.state.terraform_completed_turn.items()):
            if self.state.turn - tdone >= GC.terraform_decay_delay:
                self.state.terraforming[cell] = max(0.0, self.state.terraforming.get(cell, 0.0) - GC.terraform_decay_per_turn)

    def _phase_respawn(self) -> None:
        for pid, player in self.state.players.items():
            if player.main_id not in self.state.plantations:
                own = [p for p in self.state.plantations.values() if p.owner_id == pid]
                for p in own:
                    del self.state.plantations[p.id]
                player.score = max(0.0, player.score * 0.95 - 1)
                spawn = (0, pid) if pid % 2 == 0 else (self.state.width - 1, self.state.height - 1 - pid)
                new_main = self.state.spawn_plantation(pid, spawn)
                player.main_id = new_main
        update_all_connectivity(self.state)

    def _phase_weather(self) -> None:
        r = self.state.rng()
        if r.random() < GC.earthquake_prob:
            for p in self.state.plantations.values():
                p.hp -= GC.earthquake_damage
            for c in self.state.constructions.values():
                c.hp -= GC.earthquake_damage
        if not self.state.weather.sandstorm_active and r.random() < GC.sandstorm_prob:
            self.state.weather.sandstorm_active = True
            self.state.weather.sandstorm_age = 0
            self.state.weather.sandstorm_center = (0, 0)
        if self.state.weather.sandstorm_active:
            self.state.weather.sandstorm_age += 1
            cx = min(self.state.width - 1, self.state.weather.sandstorm_age)
            cy = min(self.state.height - 1, self.state.weather.sandstorm_age)
            self.state.weather.sandstorm_center = (cx, cy)
            for p in self.state.plantations.values():
                if in_square_radius(p.pos, self.state.weather.sandstorm_center, 1):
                    p.hp = max(1, p.hp - GC.sandstorm_damage)
            if self.state.weather.sandstorm_age > max(self.state.width, self.state.height):
                self.state.weather.sandstorm_active = False
