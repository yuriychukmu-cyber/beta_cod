from datssol.cli import load_yaml


def test_load_yaml_missing_returns_empty() -> None:
    assert load_yaml('not_exists.yaml') == {}
