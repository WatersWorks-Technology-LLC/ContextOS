"""Crash-safe, multi-process-safe read-modify-write for the JSON-backed stores."""
import fcntl
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict


def load_json(path: Path) -> Dict[str, Any]:
    """Read a JSON object; a corrupt file is moved aside (never silently overwritten)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    backup = path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}")
    try:
        os.replace(path, backup)
    except OSError:
        pass
    return {}


def update_json(path: Path, mutate: Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
    """Under an exclusive lock: reload from disk, apply `mutate`, atomically replace."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            data = load_json(path)
            mutate(data)
            tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, path)
            return data
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
