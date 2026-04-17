from datssol.game.simulator import DatsSolSimulator, SimulatorConfig
from datssol.planner.turn_planner import TurnPlanner


def test_planner_returns_turn() -> None:
    sim = DatsSolSimulator(SimulatorConfig(players=1))
    planner = TurnPlanner()
    cmd = planner.plan(sim.state, 0)
    assert cmd.player_id == 0
