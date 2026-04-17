from dataclasses import dataclass


@dataclass(slots=True)
class ArenaResponse:
    turn: int
    state: dict

    @classmethod
    def model_validate(cls, payload: dict) -> "ArenaResponse":
        return cls(turn=int(payload.get("turn", 0)), state=dict(payload.get("state", {})))


@dataclass(slots=True)
class CommandResponse:
    ok: bool
    message: str = ""

    @classmethod
    def model_validate(cls, payload: dict) -> "CommandResponse":
        return cls(ok=bool(payload.get("ok", False)), message=str(payload.get("message", "")))
