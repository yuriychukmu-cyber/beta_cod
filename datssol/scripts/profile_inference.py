import argparse
import time
from datssol.bots.neural_bot import NeuralBot
from datssol.game.simulator import DatsSolSimulator, SimulatorConfig


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=50)
    args = ap.parse_args()
    sim = DatsSolSimulator(SimulatorConfig())
    bot = NeuralBot()
    t0 = time.perf_counter()
    for _ in range(args.steps):
        _ = bot.act(sim.state, 0)
    dt = time.perf_counter() - t0
    print({"steps": args.steps, "total_sec": dt, "ms_per_step": 1000 * dt / args.steps})


if __name__ == "__main__":
    main()
