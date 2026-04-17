from datssol.types import Point


def in_bounds(p: Point, width: int, height: int) -> bool:
    return 0 <= p[0] < width and 0 <= p[1] < height


def ortho_neighbors(p: Point, width: int, height: int) -> list[Point]:
    x, y = p
    candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [q for q in candidates if in_bounds(q, width, height)]


def in_square_radius(a: Point, b: Point, r: int) -> bool:
    return abs(a[0] - b[0]) <= r and abs(a[1] - b[1]) <= r
