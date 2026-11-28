"""Crash-safe, multi-process-safe persistence for dict-of-records JSON files."""
import fcntl
import json
import os
from pathlib import Path
from typing import Any, Dict


def _read(path: Path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        return {}


def merge_save(path: Path, records: Dict[str, Any]) -> Dict[str, Any]:
    """Merge ``records`` into the file on disk under an exclusive lock and write atomically.

    Records written by other processes since this process loaded the file are
    preserved (per-key last-writer-wins); the write goes to a temp file that is
    fsynced and renamed so a crash can never leave a truncated file behind.
    Returns the merged mapping.
    """
    path = Path(path)
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            merged = _read(path)
            merged.update(records)
            tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            return merged
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
