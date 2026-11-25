"""Shared crash-safe, multi-process-safe JSON file persistence helpers."""
import fcntl
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict


def read_json(path: Path) -> Dict[str, Any]:
    """Read a JSON object. A corrupt file is moved aside (never silently discarded)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    try:
        path.replace(path.with_name(f"{path.name}.corrupt-{int(time.time())}"))
    except OSError:
        pass
    return {}


def locked_update(path: Path, mutate: Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
    """Re-read the file under an exclusive lock, apply ``mutate``, write atomically.

    Re-reading prevents one process overwriting another's writes with a stale
    in-memory copy; the temp-file + os.replace write prevents torn files.
    """
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            data = read_json(path)
            mutate(data)
            tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            return data
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
