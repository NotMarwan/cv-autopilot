import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

REQUIRED_FIELDS = [
    ("user", "name"), ("user", "email"), ("user", "phone"),
    ("user", "linkedin"), ("user", "location_current"), ("user", "location_target"),
]


class ConfigError(Exception):
    pass


def get_project_root() -> Path:
    return PROJECT_ROOT


def load_config(path=None) -> dict:
    path = Path(path) if path else PROJECT_ROOT / "config.json"
    if not path.exists():
        raise ConfigError(
            f"config.json not found at {path}. Run: python setup_wizard.py"
        )
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    for section, key in REQUIRED_FIELDS:
        if not config.get(section, {}).get(key):
            raise ConfigError(f"Missing required field: {section}.{key}")
    return config
