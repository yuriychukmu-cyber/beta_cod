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
        token_prefix: str | None = None,
    ) -> None:
        self.base_url = base_url or os.getenv("DATSSOL_API_BASE_URL", "http://localhost:8080")
        self.token = token or os.getenv("DATSSOL_API_TOKEN", "")
        self.auth_header = auth_header or os.getenv("DATSSOL_API_AUTH_HEADER", "X-Auth-Token")
        self.token_prefix = token_prefix if token_prefix is not None else os.getenv("DATSSOL_API_TOKEN_PREFIX", "")
        self.mock = mock
        self._mock_sim = DatsSolSimulator(SimulatorConfig()) if mock else None
        if not self.mock and not self.token:
            LOG.warning("DATSSOL_API_TOKEN is empty; authenticated requests may fail.")

    def _build_url(self, path: str) -> str:
        """Build endpoint URL from either API root or full endpoint base URL."""
        clean_path = path if path.startswith("/") else f"/{path}"
        raw = self.base_url.rstrip("/")
        if raw.endswith(clean_path):
            return raw
        root = raw
        for suffix in ("/arena", "/command", "/logs"):
            if root.endswith(suffix):
                root = root[: -len(suffix)]
                break
        return f"{root}{clean_path}"

    def _headers(self, *, json_content: bool = False) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.token:
            headers[self.auth_header] = f"{self.token_prefix}{self.token}" if self.token_prefix else self.token
        if json_content:
            headers["Content-Type"] = "application/json"
        return headers

    def get_arena(self) -> ArenaResponse:
        if self.mock and self._mock_sim is not None:
            st = self._mock_sim.state
            return ArenaResponse(turn=st.turn, state={"width": st.width, "height": st.height, "turn": st.turn})
        url = self._build_url("/arena")
        if httpx is not None:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=self._headers())
                res.raise_for_status()
                return ArenaResponse.model_validate(res.json())
        req = request.Request(url, headers=self._headers())
        with request.urlopen(req, timeout=10.0) as resp:
            return ArenaResponse.model_validate(json.loads(resp.read().decode("utf-8")))

    def post_command(self, cmd: TurnCommand) -> CommandResponse:
        payload = serialize_turn_command(cmd)
        if self.mock and self._mock_sim is not None:
            self._mock_sim.step({cmd.player_id: cmd})
            return CommandResponse(ok=True, message="mock accepted")
        url = self._build_url("/command")
        if httpx is not None:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=self._headers(json_content=True))
                res.raise_for_status()
                return CommandResponse.model_validate(res.json())
        req = request.Request(
            url,
            method="POST",
            headers=self._headers(json_content=True),
            data=json.dumps(payload).encode("utf-8"),
        )
        with request.urlopen(req, timeout=10.0) as resp:
            return CommandResponse.model_validate(json.loads(resp.read().decode("utf-8")))

    def get_logs(self) -> dict:
        if self.mock:
            return {"mode": "mock", "turn": self._mock_sim.state.turn if self._mock_sim else 0}
        url = self._build_url("/logs")
        if httpx is not None:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=self._headers())
                res.raise_for_status()
                return res.json()
        req = request.Request(url, headers=self._headers())
        with request.urlopen(req, timeout=10.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
