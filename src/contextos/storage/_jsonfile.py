"""Crash-safe, multi-process-safe helpers for the JSON-backed stores."""
import json
import logging
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None

log = logging.getLogger(__name__)


def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON object. A corrupt file is moved aside (never silently discarded)."""
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
        except OSError:
            log.error("Cannot read %s (%s) and could not back it up", path, exc)
            return {}
        log.error("Corrupt store %s (%s); preserved as %s", path, exc, backup)
        return {}


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
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


@contextmanager
def file_lock(path: Path):
    """Exclusive inter-process lock held on a sidecar `<name>.lock` file."""
    if fcntl is None:
        yield
        return
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


@contextmanager
def locked_update(path: Path, store: Dict[str, Any]):
    """Lock, refresh `store` in place from disk, let caller mutate it, then write atomically."""
    with file_lock(path):
        fresh = load_json(path)
        store.clear()
        store.update(fresh)
        yield store
        atomic_write_json(path, store)
