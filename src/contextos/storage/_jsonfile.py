"""Crash-safe, multi-process-safe helpers for the whole-file JSON stores."""
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None


def load_json_dict(path: Path) -> dict:
    """Read a JSON object; a corrupt file is moved aside (never silently overwritten)."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    try:
        os.replace(path, path.with_name(path.name + f".corrupt-{os.getpid()}"))
    except OSError:
        pass
    return {}


def atomic_write_json(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@contextmanager
def file_lock(path: Path):
    """Exclusive inter-process lock held on a sidecar file."""
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lf:
        if fcntl:
            fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(lf, fcntl.LOCK_UN)
