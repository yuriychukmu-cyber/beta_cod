# DatsSol repository invariants

## Engineering rules
- Keep simulator deterministic for a fixed seed.
- Encode ambiguous game behavior in `docs/assumptions.md` and isolate constants in `datssol/constants.py`.
- Prefer simple, stable, testable implementations over cleverness.
- Public module APIs must have type hints and docstrings.

## Testing
- Add or update tests for behavior changes.
- Keep smoke tests fast (<10s for full `pytest` on CI-like machines).

## ML/RL
- Fallback behavior must work without torch-geometric.
- Planner must validate commands before emission.

## Security
- Never hardcode API tokens; use env/config only.
