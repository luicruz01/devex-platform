import typer

from devex_cli.commands.branch import branch
from devex_cli.commands.check import check
from devex_cli.commands.init import init

app = typer.Typer(
    help="DevEx CLI — Golden Path enforcement tool",
    no_args_is_help=True,
)

app.command()(init)
app.command()(branch)
app.command()(check)
