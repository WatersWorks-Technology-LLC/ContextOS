"""Regression tests for JSON-backed store data-loss / cross-scope bugs."""
import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

A = IdentityScope("codex", "ws", "project_a", "s1", "main")
B = IdentityScope("codex", "ws", "project_b", "s1", "main")


def test_source_same_content_other_identity_does_not_overwrite(tmp_path):
    ss = SourceStore(tmp_path)
    sid_a = ss.put_source("shared text", identity=A)
    sid_b = ss.put_source("shared text", identity=B)
    assert sid_a != sid_b
    assert ss.get_source(sid_a)["project_id"] == "project_a"
    assert ss.get_sources([sid_a], identity=B, allow_legacy=False) == {}
    assert sid_a in ss.get_sources([sid_a], identity=A, allow_legacy=False)


def test_commit_same_content_other_identity_does_not_overwrite(tmp_path):
    vs = ContextVersionStore(tmp_path)
    ca = vs.create_commit("ctx", [], [], "s", identity=A)
    cb = vs.create_commit("ctx", [], [], "s", identity=B)
    assert ca["commit_id"] != cb["commit_id"]
    assert vs.get_commit(ca["commit_id"])["project_id"] == "project_a"


def test_source_store_two_instances_do_not_lose_updates(tmp_path):
    s1, s2 = SourceStore(tmp_path), SourceStore(tmp_path)
    a = s1.put_source("one", identity=A)
    b = s2.put_source("two", identity=A)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(a) and fresh.get_source(b)


def test_vector_index_two_instances_do_not_lose_updates(tmp_path):
    v1, v2 = VectorIndex(tmp_path), VectorIndex(tmp_path)
    v1.add_document("d1", "alpha")
    v2.add_document("d2", "beta")
    assert set(VectorIndex(tmp_path).documents) == {"d1", "d2"}


def test_version_store_two_instances_do_not_lose_updates(tmp_path):
    v1, v2 = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    c1 = v1.create_commit("x", [], [], "s", identity=A)["commit_id"]
    c2 = v2.create_commit("y", [], [], "s", identity=A)["commit_id"]
    fresh = ContextVersionStore(tmp_path)
    assert fresh.get_commit(c1) and fresh.get_commit(c2)


def test_corrupt_file_is_quarantined_not_wiped(tmp_path):
    (tmp_path / "sources.json").write_text("{not json", encoding="utf-8")
    ss = SourceStore(tmp_path)
    ss.put_source("new", identity=A)
    quarantined = list(tmp_path.glob("sources.json.corrupt*"))
    assert quarantined and quarantined[0].read_text(encoding="utf-8") == "{not json"
    json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))
