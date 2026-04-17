import argparse
from datssol.bots.heuristic_bot import HeuristicBot
from datssol.game.simulator import DatsSolSimulator, SimulatorConfig


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=30)
    args = ap.parse_args()

    sim = DatsSolSimulator(SimulatorConfig())
    bots = {0: HeuristicBot(), 1: HeuristicBot()}
    for _ in range(args.turns):
        cmds = {pid: bot.act(sim.state, pid) for pid, bot in bots.items()}
        sim.step(cmds)
    print({pid: p.score for pid, p in sim.state.players.items()})


if __name__ == "__main__":
    main()
