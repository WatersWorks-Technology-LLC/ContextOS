"""Crash-safe, multi-process-safe JSON dict persistence shared by the JSON-backed stores."""
import fcntl
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; a corrupt file is moved aside (never silently overwritten)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("top-level JSON value is not an object")
    except Exception as exc:
        backup = path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}")
        try:
            os.replace(path, backup)
            print(f"contextos: {path} unreadable ({exc}); preserved as {backup}", file=sys.stderr)
        except OSError:
            pass
        return {}


def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def update_json_dict(path: Path, mutate: Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
    """Under an exclusive lock: reload from disk, apply `mutate`, write atomically.

    Returns the fresh state so callers can refresh their in-memory copy.
    """
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            data = load_json_dict(path)
            mutate(data)
            write_json_atomic(path, data)
            return data
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
