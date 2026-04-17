# Architecture

The repository follows a modular neuro-symbolic design:

1. `datssol/game`: simulator core and rules.
2. `datssol/features`: graph construction, masks, dataset utilities.
3. `datssol/models`: graph encoder + temporal module + policy/value heads.
4. `datssol/planner`: local action candidates + beam search planner.
5. `datssol/bots`: heuristic, random, and neural bots.
6. `datssol/train`: imitation and RL scaffolding.
7. `datssol/adapters`: HTTP API parsing/serialization with mock mode.

## Core runtime flow
- Bot receives observation.
- For neural bot: state -> graph features -> model heads -> top-k local actions.
- Planner builds legal full-turn command JSON with risk penalties.
- Simulator executes explicit phase order.

## Extensibility
- Rule assumptions are centralized in constants and assumptions docs.
- API schema adapter isolates server field mapping.
- Graph encoder has torch-geometric optional path with pure torch fallback.
