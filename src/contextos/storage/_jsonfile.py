"""Crash-safe, multi-process-safe helpers for whole-file JSON dict stores."""
import fcntl
import json
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger(__name__)


def _read(path: Path) -> Dict[str, Any]:
    """Read a JSON dict; quarantine (never discard) an unreadable file."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("top-level JSON value is not an object")
    except Exception as exc:
        quarantine = path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}")
        try:
            os.replace(path, quarantine)
        except OSError:
            log.exception("Could not quarantine unreadable %s", path)
        else:
            log.error("Unreadable %s (%s); preserved as %s", path, exc, quarantine)
        return {}


def load(path: Path) -> Dict[str, Any]:
    with _lock(path, fcntl.LOCK_SH):
        return _read(path)


@contextmanager
def _lock(path: Path, mode: int):
    with open(path.with_name(path.name + ".lock"), "a") as lf:
        fcntl.flock(lf, mode)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


@contextmanager
def transaction(path: Path):
    """Exclusive lock; yields the freshest on-disk dict, atomically saved on success."""
    with _lock(path, fcntl.LOCK_EX):
        data = _read(path)
        yield data
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
