import argparse
import os
from datssol.train.imitation import train_imitation


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", default="checkpoints/imitation.pt")
    ap.add_argument("--epochs", type=int, default=1)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    metrics = train_imitation(args.dataset, args.out, epochs=args.epochs)
    print(metrics)


if __name__ == "__main__":
    main()
