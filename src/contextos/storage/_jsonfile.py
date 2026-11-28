"""Crash-safe, multi-process-safe JSON dict persistence shared by the JSON stores."""
import fcntl
import json
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator

log = logging.getLogger(__name__)


@contextmanager
def _lock(path: Path) -> Iterator[None]:
    with open(path.with_name(path.name + ".lock"), "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _read(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("top-level JSON value is not an object")
    except Exception as exc:
        # Never let the next save silently overwrite unreadable data.
        backup = path.with_name(f"{path.name}.corrupt-{int(time.time())}")
        try:
            os.replace(path, backup)
        except OSError:
            backup = None
        log.error("Unreadable store %s (%s); preserved as %s", path, exc, backup)
        return {}


def load_json(path: Path) -> Dict[str, Any]:
    with _lock(path):
        return _read(path)


@contextmanager
def update_json(path: Path) -> Iterator[Dict[str, Any]]:
    """Reload from disk under an exclusive lock, yield for mutation, write atomically."""
    with _lock(path):
        data = _read(path)
        yield data
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
