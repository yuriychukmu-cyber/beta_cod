from datssol.train.self_play import generate_imitation_data
from datssol.constants import ACTION_TYPES


def test_generate_imitation_data_has_valid_action_labels() -> None:
    x, y = generate_imitation_data(episodes=1, turns=5, seed=42)
    assert len(x) == len(y)
    assert len(y) > 0
    assert all(0 <= int(v) < len(ACTION_TYPES) for v in y)
