from datssol.utils.geometry import in_bounds, ortho_neighbors, in_square_radius


def test_geometry_helpers() -> None:
    assert in_bounds((1, 1), 3, 3)
    assert not in_bounds((-1, 0), 3, 3)
    assert set(ortho_neighbors((1, 1), 3, 3)) == {(0, 1), (2, 1), (1, 0), (1, 2)}
    assert in_square_radius((0, 0), (2, 2), 2)
