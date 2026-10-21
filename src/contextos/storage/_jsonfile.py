"""Cross-process safe JSON file helpers (advisory lock + atomic replace)."""
import contextlib
import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    import fcntl
except ImportError:  # non-POSIX: atomic replace still applies, locking does not
    fcntl = None


@contextlib.contextmanager
def file_lock(path: Path):
    """Exclusive advisory lock held on a sidecar ``<path>.lock`` file."""
    if fcntl is None:
        yield
        return
    with open(str(path) + ".lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def read_json_dict(path: Path) -> Dict[str, Any]:
    """Load a JSON object; a missing file is empty, a corrupt file raises."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    """Write via temp file + os.replace so readers never see a truncated file."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise
