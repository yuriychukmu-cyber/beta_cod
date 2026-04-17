from dataclasses import dataclass
try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


@dataclass(slots=True)
class AppConfig:
    seed: int = 7


def load_yaml(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            if yaml is None:
                return {}
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
