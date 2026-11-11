"""Crash-safe, multi-process-safe helpers for the small JSON-backed stores."""
import contextlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

try:  # POSIX only; on other platforms we degrade to atomic-replace without locking.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


@contextlib.contextmanager
def file_lock(path: Path):
    """Exclusive inter-process lock held for a read-modify-write cycle."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as handle:
        if fcntl:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(handle, fcntl.LOCK_UN)


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object. A corrupt file is moved aside (never silently overwritten)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    with contextlib.suppress(OSError):
        os.replace(path, path.with_name(f"{path.name}.corrupt-{int(time.time())}"))
    return {}


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
