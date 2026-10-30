import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict


def read_json_dict(path: Path) -> Dict[str, Any]:
    """Read a JSON object; quarantine an unreadable file instead of letting it be overwritten."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    quarantine = path.with_name(f"{path.name}.corrupt-{int(time.time())}")
    try:
        os.replace(path, quarantine)
    except OSError:
        pass
    return {}


def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


@contextmanager
def locked_json(path: Path):
    """Exclusive cross-process read-modify-write of a JSON object file.

    Yields the freshest on-disk dict; mutate it in place. It is written atomically on exit.
    """
    with open(path.with_name(path.name + ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = read_json_dict(path)
            yield data
            write_json_atomic(path, data)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
