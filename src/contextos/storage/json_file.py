"""Shared JSON loading for small file-backed stores."""
import json
import os
import time
from pathlib import Path
from typing import Any, Dict


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; move a corrupt file aside instead of letting the
    next save silently overwrite (and thereby destroy) it."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    try:
        os.replace(path, path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}"))
    except OSError:
        pass
    return {}
