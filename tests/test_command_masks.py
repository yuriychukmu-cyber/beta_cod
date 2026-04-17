from datssol.game.simulator import DatsSolSimulator, SimulatorConfig
from datssol.utils.masks import action_mask_for_plantation


def test_mask_connected_vs_disconnected() -> None:
    sim = DatsSolSimulator(SimulatorConfig(width=8, height=8, players=1))
    s = sim.state
    p = s.players[0].main_id
    m = action_mask_for_plantation(s, 0, p)
    assert sum(m) == len(m)
