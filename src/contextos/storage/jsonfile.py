"""Crash-safe, multi-process-safe persistence for the small JSON-dict stores."""
import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def load_json_dict(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@contextmanager
def file_lock(path: Path):
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def merge_save(path: Path, current: Dict[str, Any], dirty: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """Merge `dirty` keys of `current` into the on-disk dict and write it atomically.

    Re-reading under an exclusive lock keeps records written by other processes
    since this store was loaded; the temp-file rename keeps a crash from leaving
    a truncated file (which loaders would read back as empty).
    """
    with file_lock(path):
        merged = load_json_dict(path)
        keys = list(current) if dirty is None else [k for k in dirty if k in current]
        for key in keys:
            merged[key] = current[key]
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
    return merged
