import argparse
import os
import json
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from datssol.train.self_play import generate_imitation_data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=4)
    ap.add_argument("--turns", type=int, default=30)
    ap.add_argument("--out", type=str, default="data/imitation_dataset.npz")
    args = ap.parse_args()
    x, y = generate_imitation_data(episodes=args.episodes, turns=args.turns)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    if np is not None:
        np.savez(args.out, x=x, y=y)
    else:
        if not args.out.endswith(".json"):
            args.out = args.out + ".json"
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"x": x, "y": y}, f)
    print(f"saved {len(x)} samples to {args.out}")


if __name__ == "__main__":
    main()
