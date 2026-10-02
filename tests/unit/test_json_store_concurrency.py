import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex


def _ident():
    return IdentityScope(runtime_id="codex", workspace_id="w", project_id="p", session_id="s", agent_id="main")


def test_source_store_two_writers_do_not_lose_updates(tmp_path):
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)  # second process sharing the same file
    a.put_source("alpha", source_id="A", identity=_ident())
    b.put_source("beta", source_id="B", identity=_ident())
    on_disk = json.loads((tmp_path / "sources.json").read_text())
    assert set(on_disk) == {"A", "B"}


def test_vector_index_two_writers_do_not_lose_updates(tmp_path):
    a = VectorIndex(tmp_path)
    b = VectorIndex(tmp_path)
    a.add_document("A", "alpha text")
    b.add_document("B", "beta text")
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"A", "B"}


def test_corrupt_store_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=_ident())
    backups = list(tmp_path.glob("sources.json.corrupt*"))
    assert backups and backups[0].read_text() == "{not json"
