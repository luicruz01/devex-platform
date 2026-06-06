import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from devex_cli.config.loader import (
    DEFAULT_WORK_ID_PATTERN,
    ConfigLoader,
    ConfigNotFoundError,
)
from devex_cli.dora.emitter import DoraEmitter

console = Console()

CheckStatus = Literal["pass", "fail", "skipped"]


def _run_git(args: list[str]) -> str | None:
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _branch_contains_work_id(branch: str | None, pattern: str) -> CheckStatus:
    if not branch:
        return "fail"
    core = pattern.lstrip("^").rstrip("$")
    return "pass" if re.search(core, branch) else "fail"


def _commit_message_valid(message: str | None, pattern: str) -> CheckStatus:
    if not message:
        return "fail"
    core = pattern.lstrip("^").rstrip("$")
    if re.match(rf"^{core}(?::|\s|$)", message):
        return "pass"
    return "fail"


def _run_lint(stack: str) -> CheckStatus:
    if stack == "python" or stack.startswith("python"):
        if not shutil.which("ruff"):
            return "skipped"
        result = subprocess.run(
            ["ruff", "check", "."],
            capture_output=True,
            text=True,
        )
        return "pass" if result.returncode == 0 else "fail"

    if stack == "typescript" or stack.startswith("typescript"):
        if not shutil.which("eslint"):
            return "skipped"
        result = subprocess.run(
            ["eslint", "."],
            capture_output=True,
            text=True,
        )
        return "pass" if result.returncode == 0 else "fail"

    return "skipped"


def _status_label(status: CheckStatus) -> str:
    labels = {
        "pass": "[green]✓ pass[/green]",
        "fail": "[red]✗ fail[/red]",
        "skipped": "[yellow]- skipped[/yellow]",
    }
    return labels[status]


def check(path: str = ".") -> None:
    """Run Golden Path checks on the current repository."""
    start = time.monotonic()
    target = Path(path).resolve()
    original_cwd = Path.cwd()
    try:
        os.chdir(target)

        try:
            config = ConfigLoader.load()
        except ConfigNotFoundError:
            config = {
                "work_id_pattern": DEFAULT_WORK_ID_PATTERN,
                "stack": "unknown",
            }

        pattern = config.get("work_id_pattern", DEFAULT_WORK_ID_PATTERN)
        stack = config.get("stack", "unknown")
        work_id = config.get("work_id", "N/A")

        current_branch = _run_git(["branch", "--show-current"])
        commit_message = _run_git(["log", "-1", "--pretty=%s"])

        results: list[tuple[str, CheckStatus]] = [
            ("Work ID in branch", _branch_contains_work_id(current_branch, pattern)),
            ("Commit message", _commit_message_valid(commit_message, pattern)),
            ("Lint", _run_lint(stack)),
        ]

        table = Table(title="DevEx Check Results")
        table.add_column("Check", style="cyan")
        table.add_column("Result")
        for name, status in results:
            table.add_row(name, _status_label(status))
        console.print(table)

        all_ok = all(s in ("pass", "skipped") for _, s in results)
        duration_ms = int((time.monotonic() - start) * 1000)
        event = DoraEmitter.build_event(
            work_id=work_id,
            stage="check",
            status="success" if all_ok else "failure",
            team=config.get("team", "platform"),
            stack=stack,
            duration_ms=duration_ms,
            failure_reason=None if all_ok else "check-failed",
        )
        DoraEmitter.emit(event)

        if not all_ok:
            raise typer.Exit(code=1)
    finally:
        os.chdir(original_cwd)
