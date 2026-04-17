from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from datssol.bots.heuristic_bot import HeuristicBot
from datssol.constants import ACTION_TYPES
from datssol.game.commands import TurnCommand
from datssol.game.simulator import DatsSolSimulator, SimulatorConfig
from datssol.features.node_features import build_node_features


def _action_type_label_for_author(sim: DatsSolSimulator, cmd: TurnCommand, author_id: int) -> int:
    action = next((a for a in cmd.actions if a.author_id == author_id), None)
    if action is None:
        return ACTION_TYPES.index("noop")
    if isinstance(action.target, tuple):
        return ACTION_TYPES.index("build")
    if isinstance(action.target, int):
        if action.target in sim.state.plantations:
            trg = sim.state.plantations[action.target]
            return ACTION_TYPES.index("repair") if trg.owner_id == cmd.player_id else ACTION_TYPES.index("sabotage")
        if action.target in sim.state.beaver_lairs:
            return ACTION_TYPES.index("attack_beaver")
    return ACTION_TYPES.index("noop")


def generate_imitation_data(episodes: int = 4, turns: int = 40, seed: int = 7) -> tuple[Any, Any]:
    xs: list[Any] = []
    ys: list[int] = []
    for ep in range(episodes):
        sim = DatsSolSimulator(SimulatorConfig(seed=seed + ep))
        bots = {0: HeuristicBot(), 1: HeuristicBot()}
        for _ in range(turns):
            x0, ids0 = build_node_features(sim.state, 0)
            cmds = {pid: bot.act(sim.state, pid) for pid, bot in bots.items()}
            # Per-plantation behavioral labels for player 0
            if len(ids0):
                for row_idx, pid in enumerate(ids0):
                    plantation = sim.state.plantations.get(pid)
                    if plantation is None or plantation.owner_id != 0:
                        continue
                    if np is None:
                        xs.append(x0[row_idx])
                    else:
                        xs.append(x0[row_idx].copy())
                    ys.append(_action_type_label_for_author(sim, cmds[0], pid))
            sim.step(cmds)
    if np is None:
        return xs, ys  # type: ignore[return-value]
    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.int64)
