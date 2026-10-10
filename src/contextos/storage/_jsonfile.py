"""Crash-safe, multi-process-safe helpers for the whole-file JSON stores."""
import fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; a corrupt file is moved aside (never silently discarded)."""
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
        os.replace(path, path.with_name(f"{path.name}.corrupt-{int(time.time())}"))
    except OSError:
        pass
    return {}


@contextmanager
def locked(path: Path):
    """Exclusive cross-process lock for a read-modify-write cycle on `path`."""
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
