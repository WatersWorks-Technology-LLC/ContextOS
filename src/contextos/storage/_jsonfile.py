"""Cross-process safe read-modify-write for the JSON-backed stores."""
import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


def read_json(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


@contextmanager
def locked_update(path: Path):
    """Yield the current on-disk dict under an exclusive lock; persist it atomically on exit.

    Re-reading inside the lock keeps updates made by other processes since this
    store was constructed, and the temp-file + rename means a crash never leaves a
    truncated file behind (which loaders would treat as empty and then overwrite).
    """
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = read_json(path)
            yield data
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                os.replace(tmp, path)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
