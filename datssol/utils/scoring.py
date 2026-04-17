from datssol.constants import GC
from datssol.types import Point


def cell_score_cap(cell: Point) -> int:
    return GC.boosted_cell_max_score if cell[0] % GC.boosted_modulo == 0 and cell[1] % GC.boosted_modulo == 0 else GC.regular_cell_max_score
