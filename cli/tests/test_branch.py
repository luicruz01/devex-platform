from devex_cli.commands.branch import build_branch_name
from devex_cli.config.loader import ConfigLoader, DEFAULT_WORK_ID_PATTERN


def test_valid_work_id_passes() -> None:
    assert ConfigLoader.validate_work_id("FIN-123", DEFAULT_WORK_ID_PATTERN)


def test_invalid_work_id_fails() -> None:
    assert not ConfigLoader.validate_work_id("123-FIN", DEFAULT_WORK_ID_PATTERN)


def test_branch_name_format() -> None:
    assert build_branch_name("FIN-123", "feat/retry") == "FIN-123/feat/retry"


def test_custom_pattern() -> None:
    pattern = r"^PROJ-\d{4}$"
    assert ConfigLoader.validate_work_id("PROJ-1234", pattern)
    assert not ConfigLoader.validate_work_id("PROJ-12", pattern)
