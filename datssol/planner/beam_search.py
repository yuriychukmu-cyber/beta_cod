from dataclasses import dataclass
from datssol.types import LocalAction


@dataclass(slots=True)
class BeamItem:
    actions: list[LocalAction]
    score: float


def build_turn_with_beam(candidates: dict[int, list[LocalAction]], beam_size: int = 8) -> list[LocalAction]:
    beams = [BeamItem(actions=[], score=0.0)]
    for _, cand_list in candidates.items():
        nxt: list[BeamItem] = []
        for beam in beams:
            for c in cand_list:
                penalty = sum(1.0 for a in beam.actions if a.exit_id == c.exit_id)
                nxt.append(BeamItem(actions=beam.actions + [c], score=beam.score + c.score - penalty * 0.25))
        beams = sorted(nxt, key=lambda b: b.score, reverse=True)[:beam_size]
    return beams[0].actions if beams else []
