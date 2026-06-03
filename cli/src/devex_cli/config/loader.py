import os
import re
from pathlib import Path

import yaml

DEFAULT_WORK_ID_PATTERN = r"^[A-Z]+-\d+$"

DEFAULT_CONFIG: dict = {
    "work_id_pattern": DEFAULT_WORK_ID_PATTERN,
    "stack": "unknown",
    "environments": ["sandbox", "staging", "production"],
    "dora_destination": "cloudwatch",
    "team": "platform",
}


class ConfigNotFoundError(Exception):
    pass


class InvalidWorkIdError(Exception):
    pass


class ConfigLoader:
    @staticmethod
    def _config_path() -> Path:
        return Path.cwd() / ".devex" / "config.yaml"

    @staticmethod
    def _read_yaml_config() -> dict:
        path = ConfigLoader._config_path()
        if not path.exists():
            return {}
        with path.open() as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    @staticmethod
    def load(work_id_arg: str | None = None) -> dict:
        config = ConfigLoader._read_yaml_config()
        config_path = ConfigLoader._config_path()

        work_id: str | None = None
        if work_id_arg:
            work_id = work_id_arg
        elif os.environ.get("DEVEX_WORK_ID"):
            work_id = os.environ["DEVEX_WORK_ID"]
        elif config.get("work_id"):
            work_id = str(config["work_id"])

        if work_id:
            config["work_id"] = work_id

        if work_id or config_path.exists():
            merged = {**DEFAULT_CONFIG, **config}
            return merged

        raise ConfigNotFoundError(
            "No Work ID found. Use --work-id, set DEVEX_WORK_ID, "
            "or create .devex/config.yaml"
        )

    @staticmethod
    def validate_work_id(work_id: str, pattern: str) -> bool:
        return re.match(pattern, work_id) is not None

    @staticmethod
    def detect_stack(path: str = ".") -> str:
        base = Path(path)
        signals = [
            ("pyproject.toml", "python"),
            ("go.mod", "go"),
            ("package.json", "typescript"),
            ("deps.edn", "clojure"),
        ]
        for filename, stack in signals:
            if (base / filename).exists():
                return stack
        return "unknown"
