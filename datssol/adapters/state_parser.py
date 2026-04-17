from datssol.game.state import WorldState


def parse_arena_state(payload: dict) -> WorldState:
    # placeholder adapter; map external fields to internal WorldState when real schema is known
    return WorldState(width=payload.get("width", 12), height=payload.get("height", 12), turn=payload.get("turn", 0))
