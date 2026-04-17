# Simulator phase order

Engine phase order is implemented in `datssol/game/simulator.py` as:
1. upgrades
2. repair/build
3. sabotage
4. beaver lair attacks by players
5. relocate main
6. beaver attacks
7. isolated degradation
8. stalled construction degradation
9. terraformation and score
10. respawn
11. weather events

This order is tested in `tests/test_simulator_phases.py`.
