"""Crash-safe, multi-process-safe JSON file helpers for the JSON-backed stores."""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object. A corrupt file is preserved as <name>.corrupt-<ts>, never overwritten."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    try:
        os.replace(path, path.with_name(f"{path.name}.corrupt-{int(time.time() * 1000)}"))
    except OSError:
        pass
    return {}


@contextmanager
def locked_update(path: Path):
    """Exclusive inter-process lock; yields the freshly re-read data. Caller mutates it in place."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a+") as lock:
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
