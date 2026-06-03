import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def init() -> None:
    console.print("devex init — coming soon")


@app.command()
def branch(work_id: str, name: str) -> None:
    console.print("devex branch — coming soon")


@app.command()
def check() -> None:
    console.print("devex check — coming soon")
