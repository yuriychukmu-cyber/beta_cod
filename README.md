# DatsSol ML/RL Agent V1

Production-style V1 repository for a **DatsSol** local simulator, heuristic + neural agents, imitation learning, and RL scaffold.

## Features
- Deterministic local simulator with explicit server phase order.
- Heuristic baseline bot and random bot.
- Neural network with graph encoder fallback (pure PyTorch).
- Turn planner with beam search and risk-aware penalties.
- Dataset generation and imitation learning training.
- MAPPO-style RL scaffold (rollout + PPO update skeleton).
- HTTP API adapter with mock mode.

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick start
```bash
python -m datssol.scripts.play_local --turns 20
python -m datssol.scripts.generate_dataset --episodes 2 --out data/demo_dataset.npz
python -m datssol.scripts.train_imitation --dataset data/demo_dataset.npz --epochs 1
python -m datssol.scripts.profile_inference --steps 20
python -m datssol.scripts.train_rl --iters 1 --horizon 16
python -m datssol.scripts.run_client --mock --turns 5
```

### Real API mode
```bash
export DATSSOL_API_BASE_URL="https://<your-server>"
export DATSSOL_API_TOKEN="<your-token>"
python -m datssol.scripts.run_client --turns 3
```
`DATSSOL_API_BASE_URL` can be either API root (e.g. `https://host/api`) or a full endpoint like `https://host/api/arena`.

You can also override from CLI (`--base-url`, `--token`, `--auth-header`) but env vars are recommended.
By default client sends token via `X-Auth-Token` header. If backend expects bearer auth, set `DATSSOL_API_AUTH_HEADER=Authorization` and `DATSSOL_API_TOKEN_PREFIX=\"Bearer \"`.

Or use local config file:
```bash
cp configs/local.example.yaml configs/local.yaml
# edit token/base_url in configs/local.yaml
python -m datssol.scripts.run_client --config configs/local.yaml --turns 3
```

## Test
```bash
pytest -q
```

## Project layout
See `docs/architecture.md` for module-level architecture, `docs/training.md` for training flow, and `docs/api_integration.md` for client integration details.
