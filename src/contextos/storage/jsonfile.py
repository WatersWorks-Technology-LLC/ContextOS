"""Process-safe persistence for dict-of-records JSON files."""
import fcntl
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def _read(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("top-level JSON value is not an object")
    except Exception:
        # Preserve the unreadable file for recovery instead of silently
        # overwriting it on the next save.
        try:
            os.replace(path, path.with_name(path.name + ".corrupt"))
        except OSError:
            pass
        return {}


def load_json_dict(path: Path) -> Dict[str, Any]:
    return _read(path)


def merge_save(path: Path, cache: Dict[str, Any], keys: Optional[Iterable[str]] = None) -> None:
    """Merge ``keys`` of ``cache`` (all if None) into the on-disk file under an
    exclusive lock, write atomically, and refresh ``cache`` in place so records
    written by other processes are not lost."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            merged = _read(path)
            for k in (list(cache) if keys is None else keys):
                if k in cache:
                    merged[k] = cache[k]
            tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
            os.replace(tmp, path)
            cache.clear()
            cache.update(merged)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
