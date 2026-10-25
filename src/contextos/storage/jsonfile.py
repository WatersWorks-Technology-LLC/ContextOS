"""Process-safe JSON dict persistence shared by the file-backed stores."""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional


@contextmanager
def file_lock(path: Path):
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def load_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; a corrupt file is moved aside (never silently overwritten)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    path.replace(path.with_name(f"{path.name}.corrupt-{int(time.time())}-{os.getpid()}"))
    return {}


def merge_save(path: Path, current: Dict[str, Any], changed: Optional[set] = None) -> Dict[str, Any]:
    """Under an exclusive lock, merge `current` over the on-disk dict and atomically replace the file.

    `changed` limits the overlay to those keys (so a stale instance cannot revert other
    writers' entries); None overlays every in-memory key. Returns the merged dict.
    """
    with file_lock(path):
        merged = load_dict(path)
        for key, value in current.items():
            if changed is None or key in changed:
                merged[key] = value
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        tmp.replace(path)
        return merged
