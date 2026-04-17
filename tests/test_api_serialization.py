from datssol.adapters.command_serializer import serialize_turn_command
from datssol.adapters.api_client import DatsSolApiClient
from datssol.game.commands import PlantationCommand, TurnCommand


def test_serialize() -> None:
    d = serialize_turn_command(TurnCommand(player_id=1, actions=[PlantationCommand(author_id=1, exit_id=1, target=(1, 2))]))
    assert d["player_id"] == 1
    assert d["actions"][0]["path"][0] == 1


def test_api_headers() -> None:
    c = DatsSolApiClient(mock=True, token="abc")
    h = c._headers()
    assert "Authorization" in h
