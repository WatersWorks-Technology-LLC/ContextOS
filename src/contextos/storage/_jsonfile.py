"""Crash-safe, multi-process-safe helpers for the whole-file JSON stores."""
import contextlib
import fcntl
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger(__name__)


def load_json(path: Path) -> Dict[str, Any]:
    """Read a JSON object; a corrupt file is moved aside (never silently discarded)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        log.error("Corrupt store %s (%s); quarantining", path, exc)
    else:
        log.error("Store %s is not a JSON object; quarantining", path)
    backup = path.with_name(f"{path.name}.corrupt-{time.time_ns()}")
    try:
        os.replace(path, backup)
    except OSError:
        log.exception("Could not quarantine %s", path)
    return {}


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write via a temp file + rename so a crash never leaves a truncated store."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


@contextlib.contextmanager
def file_lock(path: Path):
    """Exclusive inter-process lock guarding a read-modify-write of `path`."""
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
