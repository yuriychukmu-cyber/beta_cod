import argparse
import torch
from torch import nn
from datssol.train.mappo import MAPPOTrainer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=1)
    ap.add_argument("--horizon", type=int, default=16)
    args = ap.parse_args()

    actor = nn.Linear(8, 4)
    critic = nn.Linear(8, 1)
    trainer = MAPPOTrainer(actor, critic)
    for _ in range(args.iters):
        ratio = torch.ones(args.horizon)
        adv = torch.randn(args.horizon)
        vals = torch.randn(args.horizon)
        rets = vals + torch.randn(args.horizon) * 0.1
        ent = torch.rand(args.horizon)
        print(trainer.update(ratio, adv, vals, rets, ent))


if __name__ == "__main__":
    main()
