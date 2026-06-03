from pathlib import Path

import yaml

from devex_cli.commands.check import _branch_contains_work_id, _commit_message_valid
from devex_cli.config.loader import ConfigLoader, DEFAULT_WORK_ID_PATTERN


def test_work_id_pattern_default() -> None:
    assert ConfigLoader.validate_work_id("FIN-123", DEFAULT_WORK_ID_PATTERN)
    assert not ConfigLoader.validate_work_id("fin-123", DEFAULT_WORK_ID_PATTERN)
    assert _branch_contains_work_id("FIN-123/feat/retry", DEFAULT_WORK_ID_PATTERN) == "pass"
    assert _commit_message_valid("FIN-123: add retry logic", DEFAULT_WORK_ID_PATTERN) == "pass"


def test_work_id_pattern_custom() -> None:
    pattern = r"^PROJ-\d{4}$"
    assert ConfigLoader.validate_work_id("PROJ-1234", pattern)
    assert _branch_contains_work_id("PROJ-1234/feature", pattern) == "pass"
    assert _commit_message_valid("PROJ-1234: ship it", pattern) == "pass"


def test_config_resolution_env_var(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEVEX_WORK_ID", "FIN-456")
    config = ConfigLoader.load()
    assert config["work_id"] == "FIN-456"


def test_config_resolution_priority(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    devex_dir = tmp_path / ".devex"
    devex_dir.mkdir()
    config_data = {"work_id": "YAML-001", "work_id_pattern": DEFAULT_WORK_ID_PATTERN}
    with (devex_dir / "config.yaml").open("w") as f:
        yaml.dump(config_data, f)
    monkeypatch.setenv("DEVEX_WORK_ID", "ENV-002")
    config = ConfigLoader.load(work_id_arg="ARG-003")
    assert config["work_id"] == "ARG-003"

    config_env = ConfigLoader.load()
    assert config_env["work_id"] == "ENV-002"

    monkeypatch.delenv("DEVEX_WORK_ID", raising=False)
    config_yaml = ConfigLoader.load()
    assert config_yaml["work_id"] == "YAML-001"
