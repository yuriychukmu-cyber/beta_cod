from datssol.bots.heuristic_bot import HeuristicBot
from datssol.game.models import PlayerStats
from datssol.game.state import WorldState


def _make_world() -> WorldState:
    s = WorldState(width=10, height=10)
    s.players[0] = PlayerStats(player_id=0)
    s.players[1] = PlayerStats(player_id=1)
    mid = s.spawn_plantation(0, (1, 1))
    s.players[0].main_id = mid
    return s


def test_heuristic_prefers_boosted_build_when_available() -> None:
    s = _make_world()
    bot = HeuristicBot()
    cmd = bot.act(s, 0)
    assert cmd.actions, "bot must emit non-empty action"
    # (0,0) is boosted and reachable within AR=2 from (1,1)
    assert any(a.target == (0, 0) for a in cmd.actions)


def test_heuristic_uses_upgrade_when_points_exist() -> None:
    s = _make_world()
    s.players[0].upgrade_bank = 1
    bot = HeuristicBot()
    cmd = bot.act(s, 0)
    assert cmd.upgrade is not None
