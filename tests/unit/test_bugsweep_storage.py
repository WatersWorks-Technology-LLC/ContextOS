import json
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.semantic_store import SemanticStore
from contextos.storage.source_store import SourceStore


def test_promote_assertion_creates_promoted_record(tmp_path):
    store = SemanticStore(tmp_path)
    store.add_assertion("A1", "svc", "uses", "oauth", scope="session", origin_session="s1",
                        origin_turn="t1", project_id="p")
    pid = store.promote_assertion("A1", "project")
    assert pid and pid.startswith("AST-PROM-")
    with store._get_conn() as conn:
        row = dict(conn.execute("SELECT * FROM assertions WHERE assertion_id = ?", (pid,)).fetchone())
    assert row["scope"] == "project"
    assert row["origin_assertion_id"] == "A1"
    assert row["origin_turn"] == "t1"


def test_source_store_concurrent_writers_do_not_lose_sources(tmp_path):
    ident = IdentityScope("codex", "ws", "p", "s")
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)  # second process / adapter sharing the same file
    sa = a.put_source("alpha", identity=ident)
    sb = b.put_source("beta", identity=ident)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sa) is not None
    assert fresh.get_source(sb) is not None


def test_source_store_same_content_other_identity_does_not_rebind(tmp_path):
    owner = IdentityScope("codex", "ws", "proj_a", "s")
    other = IdentityScope("codex", "ws", "proj_b", "s")
    store = SourceStore(tmp_path)
    sid = store.put_source("shared text", identity=owner)
    sid2 = store.put_source("shared text", identity=other)
    assert store.get_sources([sid], identity=owner)
    assert sid2 != sid
    assert store.get_sources([sid2], identity=other)


def test_source_store_corrupt_file_is_not_silently_overwritten(tmp_path):
    ident = IdentityScope("codex", "ws", "p", "s")
    path = tmp_path / "sources.json"
    path.write_text("{not json", encoding="utf-8")
    store = SourceStore(tmp_path)
    store.put_source("new", identity=ident)
    backups = [p for p in tmp_path.iterdir() if p.name.startswith("sources.json.corrupt")]
    assert backups and backups[0].read_text(encoding="utf-8") == "{not json"
    assert json.loads(path.read_text(encoding="utf-8"))
