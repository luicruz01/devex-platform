from pathlib import Path

from devex_cli.config.loader import ConfigLoader, DEFAULT_WORK_ID_PATTERN


def test_detect_stack_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").touch()
    assert ConfigLoader.detect_stack(str(tmp_path)) == "python"


def test_detect_stack_go(tmp_path: Path) -> None:
    (tmp_path / "go.mod").touch()
    assert ConfigLoader.detect_stack(str(tmp_path)) == "go"


def test_detect_stack_unknown(tmp_path: Path) -> None:
    assert ConfigLoader.detect_stack(str(tmp_path)) == "unknown"


def test_validate_work_id_valid() -> None:
    assert ConfigLoader.validate_work_id("FIN-123", DEFAULT_WORK_ID_PATTERN)


def test_validate_work_id_invalid() -> None:
    assert not ConfigLoader.validate_work_id("invalid", DEFAULT_WORK_ID_PATTERN)
