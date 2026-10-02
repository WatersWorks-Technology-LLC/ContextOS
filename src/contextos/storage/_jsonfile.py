"""Crash-safe, multi-process-safe JSON dict persistence helpers."""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; a corrupt file is moved aside (never silently overwritten)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    backup = path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}")
    try:
        os.replace(path, backup)
    except OSError:
        pass
    return {}


@contextmanager
def locked_update(path: Path):
    """Yield the freshest on-disk dict under an exclusive lock; atomically save it on exit."""
    with open(path.with_name(path.name + ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = load_json_dict(path)
            yield data
            tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
