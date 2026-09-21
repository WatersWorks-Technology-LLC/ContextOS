import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class StorageConfig(BaseModel):
    data_dir: Path = Field(default_factory=lambda: Path(".contextos"))
    event_store_file: str = "events.jsonl"
    source_store_file: str = "sources.json"
    semantic_db_file: str = "semantic.db"
    vector_index_file: str = "vectors.json"

class BudgetConfig(BaseModel):
    default_token_budget: int = 1500
    max_token_budget: int = 2500
    min_token_budget: int = 500

class CodecConfig(BaseModel):
    default_codec: str = "ncc_vcl"  # ncc_vcl, structured_text, json
    enable_vcl_svg: bool = False
    verification_enabled: bool = True

class ContextOSConfig(BaseModel):
    workspace_dir: Path = Field(default_factory=lambda: Path.cwd())
    client_id: str = Field(default="codex")  # 'codex', 'antigravity', 'claude_code'
    storage: StorageConfig = Field(default_factory=StorageConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    codec: CodecConfig = Field(default_factory=CodecConfig)

    @classmethod
    def load(cls, workspace_dir: Path = None, client_id: str = None) -> "ContextOSConfig":
        ws = workspace_dir or Path.cwd()
        cfg_file = ws / ".contextos" / "config.yaml"
        cid = client_id or os.getenv("CONTEXTOS_CLIENT_ID", "codex")
        if cfg_file.exists():
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                data["workspace_dir"] = ws
                data["client_id"] = cid
                return cls(**data)
            except Exception:
                pass
        return cls(workspace_dir=ws, client_id=cid)

    def ensure_directories(self) -> Path:
        return self.ensure_client_directory()

    def ensure_client_directory(self) -> Path:
        client_dir = self.workspace_dir / self.storage.data_dir / "clients" / self.client_id
        client_dir.mkdir(parents=True, exist_ok=True)
        return client_dir

    def ensure_shared_directory(self) -> Path:
        shared_dir = self.workspace_dir / self.storage.data_dir / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        return shared_dir


