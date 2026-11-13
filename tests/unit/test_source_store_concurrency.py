import json
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore

ID = IdentityScope("codex", "ws", "proj", "sess", "main")


def test_two_store_instances_do_not_lose_each_others_writes(tmp_path):
    # Two processes (hooks + MCP server) each hold their own SourceStore.
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)
    sid_a = a.put_source("content from A", identity=ID)
    sid_b = b.put_source("content from B", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sid_a) is not None, "A's write was clobbered by B"
    assert fresh.get_source(sid_b) is not None


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    path = tmp_path / "sources.json"
    path.write_text("{not valid json", encoding="utf-8")
    store = SourceStore(tmp_path)
    store.put_source("new", identity=ID)
    backups = [p for p in tmp_path.iterdir() if p.name.startswith("sources.json.corrupt")]
    assert backups and backups[0].read_text(encoding="utf-8") == "{not valid json"


def test_save_is_atomic_no_temp_leftovers(tmp_path):
    store = SourceStore(tmp_path)
    store.put_source("x", identity=ID)
    json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))
    assert not [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
