"""Safe JSON file helpers shared by the JSON-backed stores."""
import contextlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None


@contextlib.contextmanager
def file_lock(path: Path) -> Iterator[None]:
    """Cross-process exclusive lock for read-modify-write of ``path``."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lf:
        if fcntl is not None:
            fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lf, fcntl.LOCK_UN)


def load_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; a corrupt file is moved aside (never silently wiped)."""
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


def atomic_write_json(path: Path, data: Any) -> None:
    """Write via temp file + rename so readers never see a partial file."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
