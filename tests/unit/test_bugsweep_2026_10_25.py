import json
import multiprocessing

from contextos.identity import IdentityScope
from contextos.storage.semantic_store import SemanticStore
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "sess", "main")


def test_promote_assertion_creates_promoted_record(tmp_path):
    store = SemanticStore(tmp_path)
    store.add_assertion("A1", "svc", "uses", "sqlite", scope="session",
                        runtime_id="codex", workspace_id="ws", project_id="proj")
    pid = store.promote_assertion("A1", "project")
    assert pid and pid.startswith("AST-PROM-")
    rows = store.query_current_state(identity=ID)
    promoted = [r for r in rows if r["assertion_id"] == pid][0]
    assert promoted["scope"] == "project"
    assert promoted["origin_assertion_id"] == "A1"


def _put(args):
    path, i = args
    SourceStore(path).put_source(f"content {i}", source_id=f"S{i}", identity=ID)


def _add(args):
    path, i = args
    VectorIndex(path).add_document(f"D{i}", f"doc {i}")


def _commit(args):
    path, i = args
    ContextVersionStore(path).create_commit(f"ctx {i}", [], [], "s", identity=ID)


def _run(fn, path, n=12):
    with multiprocessing.get_context("spawn").Pool(4) as pool:
        pool.map(fn, [(path, i) for i in range(n)])


def test_source_store_concurrent_writers_lose_nothing(tmp_path):
    _run(_put, tmp_path)
    assert len(json.loads((tmp_path / "sources.json").read_text())) == 12


def test_vector_index_concurrent_writers_lose_nothing(tmp_path):
    _run(_add, tmp_path)
    assert len(json.loads((tmp_path / "vectors.json").read_text())) == 12


def test_version_store_concurrent_writers_lose_nothing(tmp_path):
    _run(_commit, tmp_path)
    assert len(json.loads((tmp_path / "versions.json").read_text())) == 12


def test_corrupt_store_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    store = SourceStore(tmp_path)
    store.put_source("x", identity=ID)
    assert list(tmp_path.glob("sources.json.corrupt*"))
