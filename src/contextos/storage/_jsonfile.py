"""Crash-safe, multi-process-safe helpers for the JSON-file stores."""
import contextlib
import json
import os
import tempfile
from pathlib import Path

try:  # POSIX; on platforms without fcntl we still get atomic replace.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


@contextlib.contextmanager
def file_lock(path: Path):
    """Exclusive inter-process lock held for a read-modify-write cycle."""
    lock_path = Path(str(path) + ".lock")
    with open(lock_path, "a") as lock:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(lock, fcntl.LOCK_UN)


def atomic_write_json(path: Path, data) -> None:
    """Write via temp file + os.replace so readers never see a torn file."""
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
