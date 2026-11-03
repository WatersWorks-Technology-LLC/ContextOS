import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore


def _ident():
    return IdentityScope(runtime_id="r", workspace_id="w", project_id="p", session_id="s", agent_id="a")


def test_two_store_instances_do_not_lose_writes(tmp_path):
    """Two processes (modelled as two instances) writing the same file must both persist."""
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=_ident())
    b.put_source("beta", source_id="B", identity=_ident())
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") is not None
    assert fresh.get_source("B") is not None


def test_save_is_atomic_and_leaves_no_temp_files(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=_ident())
    json.loads((tmp_path / "sources.json").read_text())
    assert [p.name for p in tmp_path.iterdir() if p.name != "sources.json" and not p.name.endswith(".lock")] == []
