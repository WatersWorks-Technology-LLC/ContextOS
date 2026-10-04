import json
import hashlib
import os
import time
from contextlib import contextmanager
try:
    import fcntl
except ImportError:  # non-POSIX
    fcntl = None
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
        self._lock_path = self.file_path.with_name(self.file_path.name + ".lock")
        self._sources: Dict[str, Dict[str, Any]] = self._load()

    @contextmanager
    def _file_lock(self):
        """Cross-process exclusive lock around read-modify-write cycles."""
        with open(self._lock_path, "a") as lock:
            if fcntl is not None:
                fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock, fcntl.LOCK_UN)

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        # Never silently discard unreadable evidence: keep a copy before it can be overwritten.
        backup = self.file_path.with_name(f"{self.file_path.name}.corrupt-{int(time.time() * 1000)}")
        try:
            os.replace(self.file_path, backup)
        except OSError:
            pass
        return {}

    def _save(self):
        tmp = self.file_path.with_name(f"{self.file_path.name}.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._sources, f, indent=2)
        os.replace(tmp, self.file_path)

    def put_source(self, content: str, source_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                   identity: Optional[IdentityScope] = None) -> str:
        if identity is None:
            raise ValueError("IdentityScope is required for new sources")
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        sid = source_id or f"SRC-{sha256}"
        with self._file_lock():
            self._sources = self._load()  # merge other writers' changes before saving
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
        self._sources = self._load()
        return self._sources.get(source_id)

    def get_sources(self, source_ids: list, max_chars: int = 12000,
                    identity: Optional[IdentityScope] = None,
                    allow_legacy: bool = True) -> Dict[str, Any]:
        self._sources = self._load()
        result = {}
        total_chars = 0
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
