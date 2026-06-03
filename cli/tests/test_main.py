from typer.testing import CliRunner

from devex_cli.main import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_init() -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
