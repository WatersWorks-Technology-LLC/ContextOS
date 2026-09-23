"""Canonical execution identity carried by ContextOS records."""
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class IdentityScope:
    runtime_id: str
    workspace_id: str
    project_id: str
    session_id: str
    agent_id: str = "main"

    @classmethod
    def from_config(cls, config: Any, session_id: str = "default", agent_id: str = "main") -> "IdentityScope":
        return cls(
            runtime_id=config.client_id,
            workspace_id=str(getattr(config, "workspace_id", None) or config.workspace_dir.resolve()),
            project_id=config.project_id,
            session_id=session_id,
            agent_id=agent_id,
        )

    @classmethod
    def from_record(cls, record: Dict[str, Any], defaults: Optional[Dict[str, str]] = None) -> "IdentityScope":
        defaults = defaults or {}
        return cls(**{
            key: record.get(key) or defaults.get(key, "LEGACY_UNKNOWN")
            for key in ("runtime_id", "workspace_id", "project_id", "session_id", "agent_id")
        })

    def as_dict(self) -> Dict[str, str]:
        return asdict(self)

    def key(self) -> str:
        return ":".join((self.runtime_id, self.workspace_id, self.project_id, self.session_id, self.agent_id))

