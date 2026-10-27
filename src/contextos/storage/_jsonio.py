"""Crash-safe, multi-process-safe helpers for the whole-file JSON stores."""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


@contextmanager
def file_lock(path: Path):
    """Exclusive advisory lock serialising read-modify-write cycles across processes."""
    with open(path.with_name(path.name + ".lock"), "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; an unreadable file is moved aside (never overwritten) and {} returned."""
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


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)
