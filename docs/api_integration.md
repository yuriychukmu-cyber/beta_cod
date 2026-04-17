# API integration

`datssol/adapters/api_client.py` exposes:
- `get_arena()`
- `post_command(payload)`
- `get_logs()`

Use env vars:
- `DATSSOL_API_BASE_URL`
- `DATSSOL_API_TOKEN`
- `DATSSOL_API_AUTH_HEADER` (optional, default `Authorization`)

Mock mode returns simulator-driven local responses for offline debugging.

`run_client.py` supports direct overrides:
- `--base-url`
- `--token`
- `--auth-header`
- `--config` (default `configs/local.yaml`)

Security note: do not commit real tokens into repository files.
