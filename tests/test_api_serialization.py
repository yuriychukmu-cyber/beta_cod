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
    assert h["X-Auth-Token"] == "abc"


def test_api_headers_with_prefix() -> None:
    c = DatsSolApiClient(mock=True, token="abc", auth_header="Authorization", token_prefix="Bearer ")
    h = c._headers()
    assert h["Authorization"] == "Bearer abc"


def test_api_url_builder_handles_root_and_endpoint() -> None:
    c_root = DatsSolApiClient(mock=True, base_url="https://games-test.datsteam.dev/api")
    assert c_root._build_url("/arena") == "https://games-test.datsteam.dev/api/arena"
    c_endpoint = DatsSolApiClient(mock=True, base_url="https://games-test.datsteam.dev/api/arena")
    assert c_endpoint._build_url("/arena") == "https://games-test.datsteam.dev/api/arena"
    assert c_endpoint._build_url("/command") == "https://games-test.datsteam.dev/api/command"
