from datssol.game.simulator import DatsSolSimulator, SimulatorConfig
from datssol.game.connectivity import update_all_connectivity


def test_connectivity_chain() -> None:
    sim = DatsSolSimulator(SimulatorConfig(width=8, height=8, players=1))
    s = sim.state
    a = s.players[0].main_id
    s.spawn_plantation(0, (1, 0))
    b = s.spawn_plantation(0, (2, 0))
    s.spawn_plantation(0, (5, 5))
    update_all_connectivity(s)
    assert s.plantations[b].connected_to_main
    isolated = [p for p in s.plantations.values() if p.pos == (5, 5)][0]
    assert not isolated.connected_to_main
