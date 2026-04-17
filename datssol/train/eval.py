from datssol.bots.heuristic_bot import HeuristicBot
from datssol.bots.neural_bot import NeuralBot
from datssol.game.commands import TurnCommand
from datssol.game.simulator import DatsSolSimulator, SimulatorConfig


def evaluate_neural_vs_heuristic(checkpoint: str | None = None, turns: int = 30) -> dict[int, float]:
    sim = DatsSolSimulator(SimulatorConfig())
    bots = {0: NeuralBot(checkpoint=checkpoint), 1: HeuristicBot()}
    for _ in range(turns):
        cmds = {pid: bot.act(sim.state, pid) for pid, bot in bots.items()}
        sim.step(cmds)
    return {pid: p.score for pid, p in sim.state.players.items()}
