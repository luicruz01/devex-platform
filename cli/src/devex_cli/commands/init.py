import os
import shutil
import sys
import time
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from devex_cli.config.loader import ConfigLoader
from devex_cli.dora.emitter import DoraEmitter

console = Console()

STACK_CONFIG_MAP = {
    "python": "python-lambda-cdk",
    "go": "go",
    "typescript": "typescript",
    "clojure": "clojure",
    "unknown": "unknown",
}

HOOK_NAMES = ("pre-commit", "pre-push")


def _hooks_source_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "hooks"


def _default_config(stack: str) -> dict:
    return {
        "work_id_pattern": "^[A-Z]+-\\d+$",
        "stack": STACK_CONFIG_MAP.get(stack, stack),
        "environments": ["sandbox", "staging", "production"],
        "dora_destination": "cloudwatch",
        "team": "platform",
    }


def init(path: str = ".") -> None:
    """Initialize DevEx Golden Path in a project directory."""
    start = time.monotonic()
    target = Path(path).resolve()
    original_cwd = Path.cwd()
    try:
        os.chdir(target)

        detected = ConfigLoader.detect_stack(str(target))
        config_stack = STACK_CONFIG_MAP.get(detected, detected)

        devex_dir = target / ".devex"
        devex_dir.mkdir(parents=True, exist_ok=True)
        config_path = devex_dir / "config.yaml"

        config_status = "created"
        if config_path.exists():
            if sys.stdin.isatty() and typer.confirm(
                f"{config_path} already exists. Overwrite?", default=False
            ):
                config_status = "overwritten"
            else:
                config_status = "skipped"

        if config_status in ("created", "overwritten"):
            with config_path.open("w") as f:
                yaml.dump(_default_config(detected), f, default_flow_style=False)

        hook_status: dict[str, str] = {name: "skipped" for name in HOOK_NAMES}
        git_dir = target / ".git"
        hooks_dir = git_dir / "hooks"

        if not git_dir.exists():
            console.print(
                "[yellow]Warning:[/yellow] No .git directory found. "
                "Git hooks were not installed."
            )
        else:
            hooks_dir.mkdir(parents=True, exist_ok=True)
            source_hooks = _hooks_source_dir()
            for hook_name in HOOK_NAMES:
                src = source_hooks / hook_name
                dest = hooks_dir / hook_name
                if src.exists():
                    shutil.copy2(src, dest)
                    dest.chmod(0o755)
                    hook_status[hook_name] = "installed"

        table = Table(title="DevEx Init Summary")
        table.add_column("Item", style="cyan")
        table.add_column("Status", style="green")
        table.add_row("Stack detected", detected)
        table.add_row("config.yaml", config_status)
        table.add_row("pre-commit", hook_status["pre-commit"])
        table.add_row("pre-push", hook_status["pre-push"])
        console.print(table)

        duration_ms = int((time.monotonic() - start) * 1000)
        event = DoraEmitter.build_event(
            work_id="N/A",
            stage="init",
            status="success",
            stack=config_stack,
            duration_ms=duration_ms,
        )
        DoraEmitter.emit(event)
    finally:
        os.chdir(original_cwd)
