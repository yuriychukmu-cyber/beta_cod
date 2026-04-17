import argparse
import os
from datssol.adapters.api_client import DatsSolApiClient
from datssol.bots.heuristic_bot import HeuristicBot
from datssol.cli import load_yaml


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--turns", type=int, default=5)
    ap.add_argument("--base-url", type=str, default=None)
    ap.add_argument("--token", type=str, default=None, help="Optional override. Prefer DATSSOL_API_TOKEN env var.")
    ap.add_argument("--auth-header", type=str, default=None, help="Defaults to Authorization.")
    ap.add_argument("--config", type=str, default="configs/local.yaml", help="Optional local yaml with api.base_url/token/auth_header.")
    args = ap.parse_args()

    cfg = load_yaml(args.config).get("api", {})
    token = args.token or cfg.get("token")
    base_url = args.base_url or cfg.get("base_url")
    auth_header = args.auth_header or cfg.get("auth_header")
    if token:
        os.environ["DATSSOL_API_TOKEN"] = token
    client = DatsSolApiClient(mock=args.mock, base_url=base_url, token=token, auth_header=auth_header)
    if args.mock:
        sim = client._mock_sim
        bot = HeuristicBot()
        for _ in range(args.turns):
            cmd = bot.act(sim.state, 0)
            print(client.post_command(cmd))
        print(client.get_logs())
    else:
        arena = client.get_arena()
        print(arena)
        print(client.get_logs())


if __name__ == "__main__":
    main()
