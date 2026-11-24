import json

from contextos.identity import IdentityScope
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def _commit(store, text):
    return store.create_commit(text, [], [], "ncc", identity=ID)["commit_id"]


def test_two_store_instances_do_not_lose_each_others_commits(tmp_path):
    a = ContextVersionStore(tmp_path)
    b = ContextVersionStore(tmp_path)
    ca = _commit(a, "alpha")
    cb = _commit(b, "beta")
    fresh = ContextVersionStore(tmp_path)
    assert fresh.get_commit(ca) is not None
    assert fresh.get_commit(cb) is not None
    assert a.get_commit(cb) is not None


def test_rollback_does_not_clobber_other_writers_commits(tmp_path):
    a = ContextVersionStore(tmp_path)
    b = ContextVersionStore(tmp_path)
    ca = _commit(a, "alpha")
    cb = _commit(b, "beta")
    a.rollback(ca)
    fresh = ContextVersionStore(tmp_path)
    assert fresh.get_commit(cb) is not None
    assert fresh.get_commit(ca)["status"] == "failed"


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    s = ContextVersionStore(tmp_path)
    _commit(s, "x")
    assert json.loads((tmp_path / "versions.json").read_text())
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"] == []


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "versions.json").write_text("{not json")
    s = ContextVersionStore(tmp_path)
    cid = _commit(s, "x")
    backups = [p for p in tmp_path.iterdir() if "corrupt" in p.name]
    assert backups and backups[0].read_text() == "{not json"
    assert cid in json.loads((tmp_path / "versions.json").read_text())
