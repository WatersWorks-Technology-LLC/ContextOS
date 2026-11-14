"""Two store instances (stand-ins for two processes) must not lose each other's writes."""
import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex


def _identity():
    return IdentityScope(runtime_id="codex", workspace_id="w", project_id="p",
                         session_id="s", agent_id="main")


def test_source_store_second_writer_keeps_first_writers_data(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=_identity())
    b.put_source("beta", source_id="B", identity=_identity())
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") is not None
    assert fresh.get_source("B") is not None


def test_vector_index_second_writer_keeps_first_writers_data(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha document")
    b.add_document("B", "beta document")
    fresh = VectorIndex(tmp_path)
    assert set(fresh.documents) == {"A", "B"}


def test_save_is_atomic_no_temp_files_left(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=_identity())
    assert json.loads((tmp_path / "sources.json").read_text())["X"]["content"] == "x"
    assert [p.name for p in tmp_path.iterdir()] == ["sources.json"]
