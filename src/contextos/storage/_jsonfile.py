"""Safe shared JSON-file persistence: cross-process lock, atomic replace, no silent wipe."""
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None


@contextmanager
def file_lock(path: Path):
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lf:
        if fcntl:
            fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(lf, fcntl.LOCK_UN)


def read_json_dict(path: Path) -> Dict[str, Any]:
    """Read a JSON object. A corrupt file is preserved as *.corrupt-<ts>, never overwritten silently."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    try:
        os.replace(path, path.with_name(f"{path.name}.corrupt-{int(time.time())}"))
    except OSError:
        pass
    return {}


def merge_save(path: Path, current: Dict[str, Any], keys: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """Under a lock, re-read disk, overlay `keys` (default all) from `current`, atomically write.

    Returns the merged dict so the caller can refresh its in-memory view.
    """
    with file_lock(path):
        merged = read_json_dict(path)
        for k in (current.keys() if keys is None else keys):
            if k in current:
                merged[k] = current[k]
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    return merged
