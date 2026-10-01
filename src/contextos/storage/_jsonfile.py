import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


def merge_save(file_path: Path, current: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist a keyed JSON store without losing concurrent writers' entries.

    Under an exclusive lock, re-reads the file, overlays this instance's entries,
    and atomically replaces the file. Returns the merged mapping.
    """
    lock_path = file_path.with_name(file_path.name + ".lock")
    with open(lock_path, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            merged: Dict[str, Any] = {}
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    merged = json.load(f)  # corrupt file raises rather than being overwritten
            merged.update(current)
            fd, tmp = tempfile.mkstemp(dir=file_path.parent, prefix=file_path.name + ".", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(merged, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, file_path)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
            return merged
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
