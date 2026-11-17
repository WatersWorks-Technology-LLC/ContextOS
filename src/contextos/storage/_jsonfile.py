"""Crash-safe, multi-process-safe read-modify-write for small JSON stores."""
import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None


@contextlib.contextmanager
def _lock(path: Path):
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lf:
        if fcntl:
            fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(lf, fcntl.LOCK_UN)


def read_json(path: Path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        return {}


def update_json(path: Path, mutate: Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
    """Under an exclusive lock: reload from disk, apply mutate, atomically replace."""
    with _lock(path):
        data = read_json(path)
        mutate(data)
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
        return data
