from datssol.game.commands import PlantationCommand, TurnCommand
from datssol.game.simulator import DatsSolSimulator, SimulatorConfig


def test_build_and_sabotage() -> None:
    sim = DatsSolSimulator(SimulatorConfig(width=10, height=10, players=2))
    s = sim.state
    p0 = s.players[0].main_id
    p1 = s.players[1].main_id
    target = (1, 0)
    for _ in range(10):
        sim.step({0: TurnCommand(player_id=0, actions=[PlantationCommand(author_id=p0, exit_id=p0, target=target)]), 1: TurnCommand(player_id=1)})
    assert any(p.owner_id == 0 and p.pos == target for p in s.plantations.values())
    new_id = [p.id for p in s.plantations.values() if p.owner_id == 0 and p.pos == target][0]
    hp_before = s.plantations[p1].hp
    sim.step({0: TurnCommand(player_id=0, actions=[PlantationCommand(author_id=new_id, exit_id=new_id, target=p1)]), 1: TurnCommand(player_id=1)})
    assert s.plantations[p1].hp <= hp_before
