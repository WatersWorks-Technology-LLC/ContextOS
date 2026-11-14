import fcntl
import json
import hashlib
import os
import threading
import contextlib
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
        self._thread_lock = threading.RLock()
        self._lock_path = self.file_path.with_name(self.file_path.name + ".lock")
        self._sources: Dict[str, Dict[str, Any]] = self._load()

    @contextlib.contextmanager
    def _locked(self):
        """Serialize read-modify-write across threads and processes."""
        with self._thread_lock:
            with open(self._lock_path, "a") as lf:
                fcntl.flock(lf, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        tmp = self.file_path.with_name(f"{self.file_path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._sources, f, indent=2)
        os.replace(tmp, self.file_path)  # atomic: readers never see a partial file

    def put_source(self, content: str, source_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                   identity: Optional[IdentityScope] = None) -> str:
        if identity is None:
            raise ValueError("IdentityScope is required for new sources")
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        # Include identity in auto-generated ids so identical content from another
        # workspace/project/session cannot overwrite (and re-own) this record.
        scope = hashlib.sha256(identity.key().encode("utf-8")).hexdigest()[:8]
        sid = source_id or f"SRC-{sha256}-{scope}"
        record = {
            "source_id": sid,
            "sha256": sha256,
            "content": content,
            "char_count": len(content),
            "metadata": metadata or {},
            **identity.as_dict(),
            "identity_confidence": "observed",
        }
        with self._locked():
            self._sources = self._load()  # merge with writes from other processes
            self._sources[sid] = record
            self._save()
        return sid

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        return self._sources.get(source_id)

    def get_sources(self, source_ids: list, max_chars: int = 12000,
                    identity: Optional[IdentityScope] = None,
                    allow_legacy: bool = True) -> Dict[str, Any]:
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
