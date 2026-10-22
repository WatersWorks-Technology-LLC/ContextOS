import json
import hashlib
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional
from ..identity import IdentityScope

class SourceStore:
    """
    Addressable raw evidence payload store keyed by SHA-256 content hash and source_id.
    """
    def __init__(self, data_dir: Path, filename: str = "sources.json"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._sources: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @contextmanager
    def _file_lock(self):
        """Cross-process exclusive lock so concurrent writers cannot lose updates."""
        lock_path = self.file_path.with_name(self.file_path.name + ".lock")
        with open(lock_path, "a+") as lock:
            try:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX)
            except ImportError:  # non-POSIX: best effort
                pass
            yield

    def _save(self):
        """Atomically replace the file (caller holds the lock)."""
        fd, tmp = tempfile.mkstemp(dir=self.file_path.parent, prefix=self.file_path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._sources, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.file_path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def put_source(self, content: str, source_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                   identity: Optional[IdentityScope] = None) -> str:
        if identity is None:
            raise ValueError("IdentityScope is required for new sources")
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        sid = source_id or f"SRC-{sha256}"
        with self._file_lock():
            self._sources = self._load()  # merge writes made by other processes
            self._put_locked(sid, sha256, content, metadata, identity)
        return sid

    def _put_locked(self, sid, sha256, content, metadata, identity):
        self._sources[sid] = {
            "source_id": sid,
            "sha256": sha256,
            "content": content,
            "char_count": len(content),
            "metadata": metadata or {}
        }
        if identity:
            self._sources[sid].update(identity.as_dict())
            self._sources[sid]["identity_confidence"] = "observed"
        self._sources[sid]["identity_confidence"] = "observed"
        self._save()

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        if source_id not in self._sources:
            self._sources = self._load()
        return self._sources.get(source_id)

    def get_sources(self, source_ids: list, max_chars: int = 12000,
                    identity: Optional[IdentityScope] = None,
                    allow_legacy: bool = True) -> Dict[str, Any]:
        result = {}
        total_chars = 0
        if any(sid not in self._sources for sid in source_ids):
            self._sources = self._load()
        for sid in source_ids:
            if sid in self._sources:
                payload = self._sources[sid]
                if identity and any(payload.get(k) != v for k, v in identity.as_dict().items()):
                    if not (allow_legacy and payload.get("identity_confidence") == "legacy"):
                        continue
                chars = len(payload["content"])
                if total_chars + chars > max_chars:
                    # Truncate
                    remaining = max_chars - total_chars
                    result[sid] = {**payload, "content": payload["content"][:remaining] + "\n[TRUNCATED]"}
                    break
                else:
                    result[sid] = payload
                    total_chars += chars
        return result
