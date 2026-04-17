import os
import json
from urllib import request
import logging

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None
from datssol.adapters.api_schema import ArenaResponse, CommandResponse
from datssol.adapters.command_serializer import serialize_turn_command
from datssol.game.commands import TurnCommand
from datssol.game.simulator import DatsSolSimulator, SimulatorConfig

LOG = logging.getLogger(__name__)


class DatsSolApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        mock: bool = False,
        auth_header: str | None = None,
    ) -> None:
        self.base_url = base_url or os.getenv("DATSSOL_API_BASE_URL", "http://localhost:8080")
        self.token = token or os.getenv("DATSSOL_API_TOKEN", "")
        self.auth_header = auth_header or os.getenv("DATSSOL_API_AUTH_HEADER", "Authorization")
        self.mock = mock
        self._mock_sim = DatsSolSimulator(SimulatorConfig()) if mock else None
        if not self.mock and not self.token:
            LOG.warning("DATSSOL_API_TOKEN is empty; authenticated requests may fail.")

    def _headers(self, *, json_content: bool = False) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.token:
            headers[self.auth_header] = f"Bearer {self.token}"
        if json_content:
            headers["Content-Type"] = "application/json"
        return headers

    def get_arena(self) -> ArenaResponse:
        if self.mock and self._mock_sim is not None:
            st = self._mock_sim.state
            return ArenaResponse(turn=st.turn, state={"width": st.width, "height": st.height, "turn": st.turn})
        if httpx is not None:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(f"{self.base_url}/arena", headers=self._headers())
                res.raise_for_status()
                return ArenaResponse.model_validate(res.json())
        req = request.Request(f"{self.base_url}/arena", headers=self._headers())
        with request.urlopen(req, timeout=10.0) as resp:
            return ArenaResponse.model_validate(json.loads(resp.read().decode("utf-8")))

    def post_command(self, cmd: TurnCommand) -> CommandResponse:
        payload = serialize_turn_command(cmd)
        if self.mock and self._mock_sim is not None:
            self._mock_sim.step({cmd.player_id: cmd})
            return CommandResponse(ok=True, message="mock accepted")
        if httpx is not None:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(f"{self.base_url}/command", json=payload, headers=self._headers(json_content=True))
                res.raise_for_status()
                return CommandResponse.model_validate(res.json())
        req = request.Request(
            f"{self.base_url}/command",
            method="POST",
            headers=self._headers(json_content=True),
            data=json.dumps(payload).encode("utf-8"),
        )
        with request.urlopen(req, timeout=10.0) as resp:
            return CommandResponse.model_validate(json.loads(resp.read().decode("utf-8")))

    def get_logs(self) -> dict:
        if self.mock:
            return {"mode": "mock", "turn": self._mock_sim.state.turn if self._mock_sim else 0}
        if httpx is not None:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(f"{self.base_url}/logs", headers=self._headers())
                res.raise_for_status()
                return res.json()
        req = request.Request(f"{self.base_url}/logs", headers=self._headers())
        with request.urlopen(req, timeout=10.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
