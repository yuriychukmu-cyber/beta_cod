from datssol.game.simulator import DatsSolSimulator, SimulatorConfig
from datssol.game.commands import TurnCommand


def test_step_increments_turn() -> None:
    sim = DatsSolSimulator(SimulatorConfig(players=1))
    t0 = sim.state.turn
    sim.step({0: TurnCommand(player_id=0)})
    assert sim.state.turn == t0 + 1
