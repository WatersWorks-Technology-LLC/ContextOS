import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.versioning import ContextVersionStore


def _ident():
    return IdentityScope(runtime_id="codex", workspace_id="w", project_id="p",
                         session_id="s", agent_id="main")


def test_source_store_two_writers_do_not_lose_updates(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # two "processes"
    ida = a.put_source("alpha", identity=_ident())
    idb = b.put_source("beta", identity=_ident())
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(ida) and fresh.get_source(idb)


def test_source_store_corrupt_file_is_quarantined_not_destroyed(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("x", identity=_ident())
    assert list(tmp_path.glob("sources.json.corrupt-*"))


def test_version_store_two_writers_do_not_lose_updates(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx-a", [], [], "s", identity=_ident())["commit_id"]
    cb = b.create_commit("ctx-b", [], [], "s", identity=_ident())["commit_id"]
    data = json.loads((tmp_path / "versions.json").read_text())
    assert ca in data and cb in data
