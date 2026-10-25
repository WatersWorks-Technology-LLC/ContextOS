"""Crash-safe, multi-process-safe helpers for the whole-file JSON stores."""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    """Read a JSON object; a corrupt file is moved aside, never silently discarded."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError):
        try:
            os.replace(path, path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}"))
        except OSError:
            pass
        return {}


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Write atomically so a crash cannot leave a truncated file."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


@contextmanager
def locked(path: Path):
    """Exclusive inter-process lock held across a read-modify-write cycle."""
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
