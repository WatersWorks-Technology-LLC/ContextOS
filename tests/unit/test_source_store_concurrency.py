import json

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def test_two_store_instances_do_not_lose_each_others_sources(tmp_path):
    # Two processes sharing shared_sources.json each hold their own SourceStore.
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)
    sid_a = a.put_source("alpha", identity=ID)
    sid_b = b.put_source("beta", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sid_a) is not None
    assert fresh.get_source(sid_b) is not None
    # a reader created earlier must also see the other writer's data
    assert a.get_source(sid_b) is not None


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", identity=ID)
    assert json.loads((tmp_path / "sources.json").read_text())
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"] == []
