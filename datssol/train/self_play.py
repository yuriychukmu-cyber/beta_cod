from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from datssol.bots.heuristic_bot import HeuristicBot
from datssol.game.simulator import DatsSolSimulator, SimulatorConfig
from datssol.features.node_features import build_node_features


def generate_imitation_data(episodes: int = 4, turns: int = 40, seed: int = 7) -> tuple[Any, Any]:
    xs: list[Any] = []
    ys: list[int] = []
    for ep in range(episodes):
        sim = DatsSolSimulator(SimulatorConfig(seed=seed + ep))
        bots = {0: HeuristicBot(), 1: HeuristicBot()}
        for _ in range(turns):
            x0, _ = build_node_features(sim.state, 0)
            if len(x0):
                if np is None:
                    cols = len(x0[0])
                    xs.append([sum(row[i] for row in x0) / len(x0) for i in range(cols)])
                else:
                    xs.append(x0.mean(axis=0))
                ys.append(1)
            cmds = {pid: bot.act(sim.state, pid) for pid, bot in bots.items()}
            sim.step(cmds)
    if np is None:
        return xs, ys  # type: ignore[return-value]
    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.int64)
