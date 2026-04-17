from __future__ import annotations

import os

import httpx


class ApiClient:
    def __init__(self) -> None:
        token = os.environ["DATSSOL_AUTH_TOKEN"]
        base_url = os.environ.get("DATSSOL_BASE_URL", "https://games-test.datsteam.dev").rstrip("/")

        self.client = httpx.Client(
            base_url=base_url,
            headers={"X-Auth-Token": token},
            timeout=10.0,
        )

    def get_arena(self):
        response = self.client.get("/api/arena")
        return self._handle_response(response)

    def post_command(self, payload: dict):
        response = self.client.post("/api/command", json=payload)
        return self._handle_response(response)

    def get_logs(self):
        response = self.client.get("/api/logs")
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: httpx.Response):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"HTTP {response.status_code} for {response.request.method} {response.request.url}\n"
                f"Response body:\n{response.text}"
            ) from exc

        try:
            return response.json()
        except Exception:
            return response.text