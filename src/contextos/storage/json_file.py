"""Crash-safe, multi-process-safe persistence for the JSON dict stores."""
import fcntl
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a dict; a corrupt file is moved aside (not silently discarded)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    shutil.copy2(path, path.with_name(f"{path.name}.corrupt-{int(time.time())}"))
    return {}


def merge_save_json_dict(path: Path, memory: Dict[str, Any]) -> None:
    """Merge `memory` over the on-disk state under a file lock, then replace atomically.

    Entries written by other processes since this process loaded are preserved;
    on key conflicts this process's entry wins.
    """
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            merged = load_json_dict(path)
            merged.update(memory)
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
            memory.update(merged)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
