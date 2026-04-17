import torch
from datssol.bots.base import Bot
from datssol.features.edge_features import build_edges
from datssol.features.node_features import build_node_features
from datssol.game.commands import TurnCommand
from datssol.game.state import WorldState
from datssol.models.checkpoints import load_checkpoint
from datssol.models.datssol_net import DatsSolNet
from datssol.planner.turn_planner import TurnPlanner


class NeuralBot(Bot):
    def __init__(self, checkpoint: str | None = None, device: str = "cpu") -> None:
        self.model = DatsSolNet()
        if checkpoint:
            load_checkpoint(self.model, checkpoint, map_location=device)
        self.model.to(device)
        self.model.eval()
        self.device = device
        self.planner = TurnPlanner()

    @torch.no_grad()
    def act(self, state: WorldState, player_id: int) -> TurnCommand:
        x_np, ids = build_node_features(state, player_id)
        if len(ids) == 0:
            return TurnCommand(player_id=player_id)
        e_np = build_edges(state, ids)
        x = torch.from_numpy(x_np).to(self.device)
        e = torch.from_numpy(e_np).to(self.device)
        out = self.model(x, e)
        node_id_to_row = {pid: i for i, pid in enumerate(ids)}
        return self.planner.plan(state, player_id, model_output=out, node_id_to_row=node_id_to_row)
