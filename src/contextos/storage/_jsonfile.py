"""Safe whole-file JSON persistence shared by the JSON-backed stores.

Several processes (e.g. different runtimes writing ``.contextos/shared``) may
open the same file, so every read-modify-write must (1) hold an inter-process
lock, (2) start from the file's current contents, and (3) replace the file
atomically so readers never see a torn write.
"""
import contextlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

try:  # POSIX only; on other platforms fall back to atomic replace without locking
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    # Unreadable: keep the bytes for recovery instead of silently overwriting them.
    try:
        os.replace(path, path.with_name(f"{path.name}.corrupt.{int(time.time() * 1000)}"))
    except OSError:
        pass
    return {}


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


@contextlib.contextmanager
def file_lock(path: Path):
    if fcntl is None:  # pragma: no cover
        yield
        return
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
