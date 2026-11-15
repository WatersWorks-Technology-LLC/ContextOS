"""Crash-safe, multi-process-safe helpers for the small JSON-file stores."""
import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


@contextmanager
def file_lock(path: Path):
    """Exclusive inter-process lock held on a sidecar ``<name>.lock`` file."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)


def read_json_dict(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write via temp file + rename so readers never see a truncated file."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
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


def merge_write(path: Path, key: str, value: Any) -> Dict[str, Any]:
    """Under lock: re-read disk, set one key, atomically write. Returns merged dict."""
    with file_lock(path):
        current = read_json_dict(path)
        current[key] = value
        atomic_write_json(path, current)
    return current
