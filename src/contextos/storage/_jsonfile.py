"""Safe cross-process read-modify-write for the small JSON-file stores."""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict


def read_json_dict(path: Path) -> Dict[str, Any]:
    """Read a JSON object; a corrupt file is quarantined (never silently discarded)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    try:
        os.replace(path, path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}"))
    except OSError:
        pass
    return {}


@contextmanager
def _locked(path: Path):
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def update_json_dict(path: Path, mutate: Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
    """Under an exclusive lock: reload from disk, apply `mutate`, atomically replace."""
    with _locked(path):
        data = read_json_dict(path)
        mutate(data)
        tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return data
