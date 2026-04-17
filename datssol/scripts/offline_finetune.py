"""One-command offline finetuning pipeline.

1) Generate imitation data from greedy heuristic self-play
2) Train imitation model
3) Evaluate neural-vs-heuristic short match
"""

import argparse
import os
import numpy as np

from datssol.train.eval import evaluate_neural_vs_heuristic
from datssol.train.imitation import train_imitation
from datssol.train.self_play import generate_imitation_data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=16)
    ap.add_argument("--turns", type=int, default=80)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--dataset", type=str, default="data/offline_imitation.npz")
    ap.add_argument("--checkpoint", type=str, default="checkpoints/offline_imitation.pt")
    ap.add_argument("--eval-turns", type=int, default=80)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.dataset), exist_ok=True)
    os.makedirs(os.path.dirname(args.checkpoint), exist_ok=True)

    x, y = generate_imitation_data(episodes=args.episodes, turns=args.turns)
    np.savez(args.dataset, x=x, y=y)
    print({"dataset": args.dataset, "samples": int(len(y))})

    metrics = train_imitation(args.dataset, args.checkpoint, epochs=args.epochs)
    print({"train": metrics, "checkpoint": args.checkpoint})

    score = evaluate_neural_vs_heuristic(args.checkpoint, turns=args.eval_turns)
    print({"eval_score": score})


if __name__ == "__main__":
    main()
