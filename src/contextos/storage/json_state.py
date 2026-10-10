"""Crash-safe, multi-process-safe persistence for the JSON-backed stores."""
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


@contextmanager
def _locked(path: Path):
    with open(str(path) + ".lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def load_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; a corrupt file is preserved aside, not silently discarded."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    path.replace(path.with_name(f"{path.name}.corrupt-{int(time.time())}"))
    return {}


def merge_save(path: Path, current: Dict[str, Any]) -> Dict[str, Any]:
    """Merge in-memory entries over what other processes wrote, then replace atomically."""
    with _locked(path):
        merged = load_dict(path)
        merged.update(current)
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    return merged
