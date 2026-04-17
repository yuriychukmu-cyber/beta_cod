from datssol.game.simulator import DatsSolSimulator, SimulatorConfig
from datssol.game.commands import TurnCommand


def test_beaver_exists_and_weather_runs() -> None:
    sim = DatsSolSimulator(SimulatorConfig(players=1, seed=1))
    assert sim.state.beaver_lairs
    for _ in range(5):
        sim.step({0: TurnCommand(player_id=0)})
    assert sim.state.turn == 5
