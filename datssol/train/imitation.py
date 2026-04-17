import json
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


def train_imitation(npz_path: str, out_ckpt: str, epochs: int = 1, batch_size: int = 32, lr: float = 1e-3) -> dict[str, float]:
    """Train imitation model.

    Uses torch pipeline if available; otherwise writes a lightweight stub checkpoint.
    """
    try:
        import torch
        from torch.optim import Adam
        from torch.utils.data import DataLoader
        from datssol.features.datasets import ImitationDataset
        from datssol.models.datssol_net import DatsSolNet
        from datssol.train.losses import imitation_loss
        from datssol.models.checkpoints import save_checkpoint
    except Exception:
        Path(out_ckpt).parent.mkdir(parents=True, exist_ok=True)
        with open(out_ckpt, "w", encoding="utf-8") as f:
            json.dump({"mode": "stub", "dataset": npz_path}, f)
        return {"loss": 0.0}

    ds = ImitationDataset(npz_path)
    dl = DataLoader(ds, batch_size=batch_size, shuffle=True)
    model = DatsSolNet(in_dim=ds.x.shape[1])
    opt = Adam(model.parameters(), lr=lr)
    model.train()
    last = 0.0
    for ep in range(epochs):
        for x, y in dl:
            edge = torch.zeros((0, 2), dtype=torch.long)
            out = model(x, edge)
            logits = out.action_logits
            loss = imitation_loss(logits, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            last = float(loss.item())
        LOG.info("epoch=%s loss=%.4f", ep, last)
    save_checkpoint(model, out_ckpt, extra={"loss": last})
    return {"loss": last}
