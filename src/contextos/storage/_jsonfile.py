"""Cross-process safe read-modify-write for the small JSON-backed stores."""
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict

try:
    import fcntl
except ImportError:  # non-POSIX: atomic replace still prevents torn files
    fcntl = None


def read_json_dict(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


@contextmanager
def locked_update(path: Path, current: Dict[str, Any]):
    """Hold an exclusive lock, refresh `current` in place from disk, then
    atomically write it back once the caller has applied its change."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lock:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            disk = read_json_dict(path)
            current.clear()
            current.update(disk)
            yield current
            tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2)
            os.replace(tmp, path)
        finally:
            if fcntl:
                fcntl.flock(lock, fcntl.LOCK_UN)
