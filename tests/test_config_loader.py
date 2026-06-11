from pathlib import Path
import sys, json, pytest
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config_loader import load_config, get_project_root, ConfigError


def test_load_valid_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "user": {
            "name": "Jane Doe", "email": "jane@example.com",
            "phone": "+1 555 000 0000", "linkedin": "linkedin.com/in/jane",
            "location_current": "Riyadh, Saudi Arabia",
            "location_target": "Riyadh, Saudi Arabia"
        },
        "projects": {"p1": "Built X. 10k users."},
        "role_project_map": {"networking": ["p1"]},
        "hunterio_api_key": ""
    }), encoding="utf-8")
    config = load_config(cfg)
    assert config["user"]["name"] == "Jane Doe"


def test_raises_if_config_missing(tmp_path):
    with pytest.raises(ConfigError, match="config.json not found"):
        load_config(tmp_path / "no_such.json")


def test_raises_if_required_field_missing(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"user": {"name": "Jane"}}), encoding="utf-8")
    with pytest.raises(ConfigError, match="user.email"):
        load_config(cfg)


def test_get_project_root_returns_path():
    root = get_project_root()
    assert (root / "src").is_dir()
