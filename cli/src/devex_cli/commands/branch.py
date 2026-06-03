import subprocess
import time

import typer
from rich.console import Console

from devex_cli.config.loader import ConfigLoader
from devex_cli.dora.emitter import DoraEmitter

console = Console()


def build_branch_name(work_id: str, name: str) -> str:
    return f"{work_id}/{name}"


def branch(work_id: str, name: str) -> None:
    """Create a git branch prefixed with the Work ID."""
    start = time.monotonic()
    try:
        config = ConfigLoader.load(work_id_arg=work_id)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    pattern = config.get("work_id_pattern", "^[A-Z]+-\\d+$")
    if not ConfigLoader.validate_work_id(work_id, pattern):
        console.print(
            f"[red]Error:[/red] Invalid Work ID '{work_id}'. "
            f"Must match pattern: {pattern}"
        )
        raise typer.Exit(code=1)

    branch_name = build_branch_name(work_id, name)
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        console.print(f"[red]Error:[/red] {stderr}")
        raise typer.Exit(code=1)

    console.print(f"[green]Created branch:[/green] {branch_name}")

    duration_ms = int((time.monotonic() - start) * 1000)
    event = DoraEmitter.build_event(
        work_id=work_id,
        stage="branch-create",
        status="success",
        team=config.get("team", "platform"),
        stack=config.get("stack", "unknown"),
        duration_ms=duration_ms,
    )
    DoraEmitter.emit(event)
