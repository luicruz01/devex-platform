from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

schema_path = Path(__file__).resolve().parent.parent.parent / "schema" / "python"
if str(schema_path) not in sys.path:
    sys.path.insert(0, str(schema_path))

if "devex_schema" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "devex_schema",
        schema_path / "__init__.py",
        submodule_search_locations=[str(schema_path)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["devex_schema"] = module
    spec.loader.exec_module(module)
